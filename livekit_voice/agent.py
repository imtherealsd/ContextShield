"""LiveKit Real-Time Voice Agent for ContextShield Security Ingestion."""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
import time
from typing import Callable, List, Optional
import uuid

from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local", override=True)

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    UserInputTranscribedEvent,
    cli,
    inference,
)
from livekit.agents.llm import StopResponse
from livekit.agents.voice import room_io

from livekit_voice.models import (
    RoomSecurityEvent,
    VoiceSecurityStatus,
    VoiceTurn,
    VoiceTurnResult,
)
from livekit_voice.shield_client import ContextShieldClient

logger = logging.getLogger("contextshield.livekit.agent")

STATIC_TRANSCRIPTION_ONLY_INSTRUCTIONS = (
    "ContextShield voice ingestion gateway. This agent operates exclusively as a "
    "speech-to-text listener and does not generate conversational responses or speech output."
)


class TranscriptionOnlyAgent(Agent):
    """Specialized LiveKit Agent that suppresses conversational LLM turn generation.
    
    ContextShield operates as a secure transcription and policy evaluation gateway.
    Raising StopResponse() indicates to the AgentSession turn pipeline that this agent
    does not synthesize conversational speech or text replies.
    """

    async def on_user_turn_completed(self, chat_ctx, new_message=None):
        raise StopResponse()


class LiveKitVoiceAgent:
    """Manages LiveKit room lifecycle, speech transcription, and ContextShield ingestion.
    
    Architecture:
    1. Audio frames received from room participant.
    2. LiveKit Inference STT transcribes speech.
    3. UserInputTranscribedEvent(is_final=True) enqueued into asyncio.Queue.
    4. Async worker processes turns sequentially preserving turn ordering.
    5. ContextShield evaluates untrusted speech before any agent sees it.
    6. Safe RoomSecurityEvent published to the LiveKit room.
    7. Only approved_context is made available to downstream agents (never raw speech).
    """

    def __init__(
        self,
        shield_client: Optional[ContextShieldClient] = None,
        stt_model: Optional[str] = None,
        stt_language: Optional[str] = None,
        on_turn_result: Optional[Callable[[VoiceTurnResult], None]] = None,
    ):
        self.shield_client = shield_client or ContextShieldClient()
        self.stt_model = stt_model or os.getenv("LIVEKIT_STT_MODEL", "deepgram/nova-3")
        self.stt_language = stt_language or os.getenv("LIVEKIT_STT_LANGUAGE", "en")
        self.on_turn_result = on_turn_result

        self._queue: asyncio.Queue[Optional[VoiceTurn]] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._last_processed_hash: Optional[str] = None
        self._last_processed_time: float = 0.0
        self._session: Optional[AgentSession] = None
        self._room: Optional[rtc.Room] = None
        self.results_history: List[VoiceTurnResult] = []

    async def start_worker(self) -> None:
        """Starts the dedicated turn processing worker maintaining strict ordering."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_turn_queue())

    async def stop_worker(self) -> None:
        """Gracefully stops the turn processing worker."""
        if self._worker_task and not self._worker_task.done():
            await self._queue.put(None)  # Sentinel to terminate
            try:
                await asyncio.wait_for(self._worker_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._worker_task.cancel()
            self._worker_task = None

    def enqueue_text(
        self,
        raw_transcript: str,
        room_name: str = "default_room",
        participant_identity: str = "user",
    ) -> None:
        """Enqueues raw text for sequential evaluation."""
        text = raw_transcript.strip() if raw_transcript else ""
        if not text:
            return

        now = time.perf_counter()
        t_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if t_hash == self._last_processed_hash and (now - self._last_processed_time) < 0.5:
            logger.debug("Deduplicated identical immediate turn: %s", t_hash[:8])
            return

        self._last_processed_hash = t_hash
        self._last_processed_time = now

        turn = VoiceTurn(
            turn_id=str(uuid.uuid4()),
            room_name=room_name,
            participant_identity=participant_identity,
            raw_transcript=text,
            transcription_completed_at=datetime.now(timezone.utc).isoformat(),
            created_at_perf=now,
        )

        try:
            self._queue.put_nowait(turn)
            logger.info(
                "Enqueued turn %s from participant %s (len=%d)",
                turn.turn_id[:8],
                participant_identity,
                len(text),
            )
        except Exception as exc:
            logger.error("Failed to queue turn: %s", exc)

    def on_transcription_event(
        self,
        ev: UserInputTranscribedEvent,
        room_name: str = "default_room",
    ) -> None:
        """Lightweight event handler called when speech is transcribed.
        
        Only queues final transcripts (is_final == True). Ignores interim partials.
        """
        if not ev.is_final:
            return

        text = ev.transcript.strip() if ev.transcript else ""
        if not text:
            return

        self.enqueue_text(
            raw_transcript=text,
            room_name=room_name,
            participant_identity=ev.speaker_id or "user",
        )

    async def _process_turn_queue(self) -> None:
        """Single-threaded consumer ensuring strict sequential turn ordering."""
        while True:
            turn = await self._queue.get()
            if turn is None:
                self._queue.task_done()
                break

            try:
                result = await self.shield_client.evaluate_turn(turn)
                self.results_history.append(result)

                logger.info(
                    "==> [TURN PROCESSED] Turn: %s | Decision: %s | Risk: %.1f | Status: %s | Approved Context: %s",
                    result.turn_id[:8],
                    result.decision,
                    result.risk_score,
                    result.status.value,
                    "YES" if result.approved_context is not None else "NONE (BLOCKED)",
                )

                # Publish safe realtime event back to LiveKit room
                await self._publish_security_event(result)

                # Invoke listener callback
                if self.on_turn_result:
                    try:
                        self.on_turn_result(result)
                    except Exception as cb_exc:
                        logger.error("Error in on_turn_result callback: %s", cb_exc)

            except Exception as exc:
                logger.error("Unexpected error evaluating voice turn %s: %s", turn.turn_id, exc)
                fail_res = VoiceTurnResult(
                    turn_id=turn.turn_id,
                    room_name=turn.room_name,
                    participant_identity=turn.participant_identity,
                    transcript_hash=hashlib.sha256(turn.raw_transcript.encode("utf-8")).hexdigest(),
                    redacted_preview=None,
                    approved_context=None,
                    status=VoiceSecurityStatus.VOICE_ERROR,
                    decision="BLOCK",
                    risk_score=100.0,
                    threat_categories=[],
                    matched_policy_ids=[],
                    moss_ms=None,
                    llm_called=False,
                    llm_status=None,
                    shield_request_id=None,
                    shield_total_ms=0.0,
                    voice_to_decision_ms=round((time.perf_counter() - turn.created_at_perf) * 1000.0, 3),
                    transcription_completed_at=turn.transcription_completed_at,
                )
                self.results_history.append(fail_res)
            finally:
                self._queue.task_done()

    async def _publish_security_event(self, result: VoiceTurnResult) -> None:
        """Publishes safe telemetry event to LiveKit room for real-time dashboard.
        
        CRITICAL PRIVACY INVARIANT:
        Payload contains only verified metadata and safe redacted preview.
        NEVER contains raw transcripts, credentials, or secrets.
        """
        # Best-effort dashboard telemetry hook (non-security-critical)
        telemetry_payload = {
            "turn_id": result.turn_id,
            "room_name": result.room_name,
            "participant_identity": result.participant_identity,
            "request_id": result.shield_request_id,
            "source": "livekit_voice",
            "decision": result.decision,
            "risk_score": result.risk_score,
            "threat_categories": result.threat_categories,
            "matched_policy_ids": result.matched_policy_ids,
            "moss_ms": result.moss_ms,
            "llm_called": result.llm_called,
            "llm_status": result.llm_status,
            "shield_total_ms": result.shield_total_ms,
            "voice_to_decision_ms": result.voice_to_decision_ms,
            "redacted_preview": result.redacted_preview,
            "approved_context_available": result.approved_context is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            from backend.app.services.dashboard_telemetry import dashboard_telemetry
            dashboard_telemetry.record_voice_event(telemetry_payload)
        except Exception:
            pass

        try:
            if hasattr(self.shield_client, "send_voice_telemetry"):
                await self.shield_client.send_voice_telemetry(telemetry_payload)
        except Exception:
            pass

        if not self._room or not self._room.local_participant:
            return

        sec_event = RoomSecurityEvent.from_voice_turn_result(result)

        payload_bytes = sec_event.model_dump_json().encode("utf-8")
        try:
            await self._room.local_participant.publish_data(
                payload_bytes,
                reliable=True,
                topic="contextshield",
            )
        except Exception as exc:
            logger.warning("Failed to publish security event to room: %s", exc)

    async def run_session(self, ctx: JobContext) -> None:
        """Sets up and runs the LiveKit AgentSession in the provided JobContext."""
        self._room = ctx.room
        await self.start_worker()

        stt_instance = inference.STT(
            model=self.stt_model,
            language=self.stt_language,
        )

        self._session = AgentSession(
            stt=stt_instance,
            turn_handling=TurnHandlingOptions(turn_detection="manual"),
        )

        # Wire event listener for speech transcription
        room_name = ctx.room.name or "contextshield-room"
        self._session.on("user_input_transcribed", lambda ev: self.on_transcription_event(ev, room_name))

        agent = TranscriptionOnlyAgent(instructions=STATIC_TRANSCRIPTION_ONLY_INSTRUCTIONS)

        async def _handle_text_input(sess: AgentSession, ev: room_io.TextInputEvent) -> None:
            if ev.text and ev.text.strip():
                part_id = ev.participant.identity if ev.participant else "<chat-user>"
                logger.info("Received text chat input from participant %s: %s", part_id, ev.text[:30])
                self.enqueue_text(
                    raw_transcript=ev.text.strip(),
                    room_name=room_name,
                    participant_identity=part_id,
                )

        room_input_opts = room_io.RoomInputOptions(
            text_input_cb=_handle_text_input,
            close_on_disconnect=False,
        )

        await self._session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=room_input_opts,
        )
        await ctx.connect()


server = AgentServer()


@server.rtc_session(agent_name="contextshield-voice")
async def entrypoint(ctx: JobContext):
    """Official LiveKit AgentServer session entrypoint."""
    voice_agent = LiveKitVoiceAgent()
    await voice_agent.run_session(ctx)


if __name__ == "__main__":
    cli.run_app(server)
