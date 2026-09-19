# ContextShield — Hackathon Submission Copy

---

## 1. Project Title
**ContextShield**

---

## 2. One-Line Tagline (123 characters)
> Low-latency security gateway inspecting untrusted external context before autonomous AI agents are permitted to consume it.

---

## 3. Short Description (88 words)
ContextShield is an open-source, defense-in-depth security gateway that protects autonomous AI agents from prompt injections, instruction overrides, and credential exfiltration hidden in external data. Positioned upstream of the agent's reasoning loop, ContextShield combines deterministic scanning, Moss semantic policy retrieval, and a gated Gemini evaluator for ambiguous edge cases. When malicious directives are detected, context is withheld completely (`approved_context = null`), ensuring the downstream agent is never invoked. ContextShield extends this strict execution boundary to real-time voice pipelines via LiveKit Cloud, delivering verifiable, privacy-safe context security.

---

## 4. Comprehensive Description (204 words)
Modern autonomous AI agents consume vast amounts of untrusted external context—from web scraping and RAG pipelines to third-party APIs and real-time voice transcripts. Because LLM architectures interleave instructions and data within a unified context window, agents cannot inherently differentiate between developer instructions and adversarial attacks embedded in external content.

ContextShield solves this vulnerability by moving the trust decision upstream of the agent. Incoming payloads pass through a measured low-latency pipeline: first, strict schema validation and deterministic scanning filter prominent attack patterns; Moss retrieves candidate enterprise security policies when configured. A calibrated Risk Engine assigns one of four canonical decisions: SAFE, SANITIZE, REVIEW, or BLOCK.

Clear cases resolve in under one millisecond without an LLM roundtrip. Only genuinely ambiguous requests escalate to a structured Gemini risk evaluator under fail-secure defaults. If context is contaminated, ContextShield either excises the hostile imperative and verifies the clean remainder (SANITIZE) or withholds context entirely (BLOCK/REVIEW), leaving the downstream agent uninvoked.

The same security boundary guards conversational voice pipelines through LiveKit Cloud and Deepgram Nova-3 STT. Backed by privacy-safe dashboard observability, ContextShield enforces a simple, powerful architectural contract: inspect first, trust second.

---

## 5. The Problem
Autonomous agents rely on external data to perform tasks, but external data is inherently untrusted. Adversaries exploit this by embedding indirect prompt injections, privilege escalation triggers, and credential exfiltration directives into web pages, API responses, and spoken dialogue. When an agent ingests raw context directly, malicious instructions compromise its reasoning loop before any post-generation guardrail can intervene.

---

## 6. The Solution
ContextShield establishes a protective perimeter between external data sources and downstream AI models. It evaluates external context across deterministic, semantic, and contextual layers, producing a clean `approved_context` payload only when the input is safe or successfully sanitized. On blocked or review-required contexts, context delivery is suppressed, preventing the downstream agent from being exposed to the attack.

---

## 7. Moss Integration
ContextShield leverages the official **Moss Python SDK** (`moss==1.12.0`) as its semantic security policy retrieval layer:
- **Index**: Pre-indexes 20 enterprise security policies in the `contextshield-security` index.
- **Measured Retrieval**: Reports observed semantic policy retrieval timing when the Moss runtime is configured and ready.
- **Evidence Separation**: The system strictly separates retrieved policy candidates from applied security evidence, ensuring similarity matches corroborate rather than fabricate decision causes.

---

## 8. LiveKit Integration
ContextShield integrates with **LiveKit Cloud** (`livekit-agents`) to protect real-time voice applications:
- **Cloud Agent Worker**: A Python 3.13 worker (`contextshield-voice`) deployed in the `ap-south` region listens to WebRTC rooms.
- **Speech-to-Text**: Employs Deepgram Nova-3 through LiveKit Inference in transcription-only mode.
- **Real-Time Evaluation**: Final speech turns are dispatched via HTTPS to the ContextShield backend. If hostile speech is spoken, context is blocked, and a privacy-safe `RoomSecurityEvent` is broadcast to the room data channel.

---

## 9. Technical Novelty
1. **Upstream Ingestion Architecture**: Positions security evaluation ahead of agent context ingestion, eliminating indirect prompt injection before model execution begins.
2. **Deterministic Fast Path**: Bypasses generative model evaluation for obvious safe and blocked contexts while exposing observed gateway processing timing.
3. **Re-Scan Sanitization Verification**: Strips malicious imperatives from valid documentation and runs a secondary deterministic scan to ensure zero hostile residue remains before downstream forwarding.
4. **Structural Agent Insulation**: The downstream `ProtectedAgent` interface structurally rejects raw context, accepting only gateway-approved strings.

---

## 10. Future Scope
- **Persistent SOC Audit Database**: Long-term event logging with PostgreSQL or ClickHouse.
- **Dynamic Policy Packs**: Web-based policy authoring and hot-reloading in Moss.
- **Human-in-the-Loop REVIEW Queue**: Webhook-driven approval flows for compliance teams.
- **Egress Tool Sandboxing**: Intercepting outbound agent tool calls and arguments.
