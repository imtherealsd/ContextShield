"""Ingest API router for ContextShield."""

import time
import uuid
from typing import List, Optional
from fastapi import APIRouter
from backend.app.models.requests import IngestRequest
from backend.app.models.responses import (
    Decision,
    IngestResponse,
    LatencyStats,
    LLMIngestStatus,
    MossIngestStatus,
    ThreatFinding,
)
from backend.app.security.risk_engine import risk_engine
from backend.app.security.scanner import DeterministicScanner
from backend.app.security.schema_gateway import GatewayContext, SchemaGateway
from backend.app.services.audit import audit_service
from backend.app.services.evaluator import evaluator_service
from backend.app.services.moss_service import moss_retriever
from backend.app.storage import AuditStorageError
import logging

router = APIRouter(prefix="/v1/shield", tags=["Ingest"])
scanner = DeterministicScanner()
logger = logging.getLogger("contextshield.ingest")


def construct_semantic_query(context: GatewayContext, findings: List[ThreatFinding]) -> str:
    """Builds a semantic query from security evidence and normalized content semantics.
    
    Adheres strictly to the requirement:
    - Includes normalized external content
    - Includes scanner threat categories and action semantics
    - Does NOT insert static policy IDs
    """
    content_summary = context.normalized_content[:350].strip()
    categories = sorted({f.category.value for f in findings})
    
    if categories:
        cat_desc = " and ".join(c.replace("_", " ") for c in categories)
        return f"Potential external {cat_desc}: {content_summary}"
    return f"Validate external untrusted context: {content_summary}"


@router.post("/ingest", response_model=IngestResponse)
async def ingest_context(request: IngestRequest) -> IngestResponse:
    """Evaluates untrusted external context through the ContextShield security pipeline.
    
    Pipeline Steps:
    1. Strict schema gateway validation and dual-buffer normalization.
    2. Deterministic Threat Scanner execution.
    3. Semantic Moss query construction and semantic policy retrieval.
    4. Deterministic Risk Engine evaluation (critical findings have absolute authority).
    5. Contextual LLM evaluation for genuinely ambiguous cases (fails secure).
    6. Privacy-first audit logging (never stores raw hostile content or LLM prompts).
    7. High-resolution monotonic timing measurement.
    """
    total_start = time.perf_counter()
    request_id = str(uuid.uuid4())

    # Step 1: Schema Gateway
    gateway_ctx = SchemaGateway.process(request)

    # Step 2: Deterministic Threat Scanner
    findings, scanner_ms = scanner.scan(gateway_ctx)

    # Step 3: Semantic Query Construction & Moss Retrieval
    semantic_query = construct_semantic_query(gateway_ctx, findings)
    moss_matches, moss_ms, query_executed = await moss_retriever.retrieve_policies(semantic_query)

    # Step 4: Deterministic Risk Engine evaluation
    (
        decision,
        risk_score,
        confidence,
        matched_policy_ids,
        sanitized_content,
        agent_context,
    ) = risk_engine.evaluate(gateway_ctx, findings, moss_matches)

    # Step 5: Contextual LLM evaluation for genuinely ambiguous cases only
    llm_ms: Optional[float] = None
    llm_state: LLMIngestStatus

    # Invocation Rule:
    # Skip LLM when:
    #   A. Deterministic CRITICAL finding exists -> BLOCK
    #   B. Strong aligned evidence already produces confident BLOCK
    #   C. Content is clearly SAFE with no meaningful security evidence
    #   D. Isolated hostile segment is safely sanitizable and verified -> SANITIZE
    # Invoke LLM ONLY for genuinely ambiguous contextual cases (decision == Decision.REVIEW)
    if decision == Decision.REVIEW:
        reason_called = "ambiguous_context"
        if not evaluator_service.configured:
            is_invalid_prov = evaluator_service.provider != "gemini"
            status_val = "invalid_provider" if is_invalid_prov else "not_configured"
            llm_state = LLMIngestStatus(
                provider=evaluator_service.provider,
                status=status_val,
                model=evaluator_service.model,
                prompt_version=evaluator_service.prompt_version,
                prompt_hash=evaluator_service.prompt_hash,
                called=False,
                reason_called=reason_called,
                target_latency_ms=getattr(evaluator_service, "target_latency_ms", 800.0),
                hard_timeout_ms=getattr(evaluator_service, "hard_timeout_ms", 1500.0),
                target_exceeded=None,
                provider_request_id=None,
            )
            llm_ms = None
            # Unconfigured or invalid provider LLM fails secure to REVIEW (decision unchanged)
        else:
            llm_eval, llm_state, measured_llm_ms = await evaluator_service.evaluate(
                source_type=request.source_type,
                untrusted_content=gateway_ctx.original_content,
                deterministic_findings=findings,
                moss_findings=moss_matches,
                reason_called=reason_called,
            )
            llm_ms = measured_llm_ms

            # Apply LLM evaluation results preserving deterministic authority
            decision, risk_score, confidence, sanitized_content, agent_context = (
                risk_engine.apply_llm_evaluation(
                    initial_decision=decision,
                    initial_risk=risk_score,
                    initial_confidence=confidence,
                    llm_eval=llm_eval,
                    findings=findings,
                    gateway_ctx=gateway_ctx,
                )
            )
    else:
        llm_state = LLMIngestStatus(
            provider=evaluator_service.provider,
            status="not_called",
            model=evaluator_service.model,
            prompt_version=evaluator_service.prompt_version,
            prompt_hash=evaluator_service.prompt_hash,
            called=False,
            reason_called=None,
            target_latency_ms=getattr(evaluator_service, "target_latency_ms", 800.0),
            hard_timeout_ms=getattr(evaluator_service, "hard_timeout_ms", 1500.0),
            target_exceeded=None,
            provider_request_id=None,
        )
        llm_ms = None

    elapsed_total = (time.perf_counter() - total_start) * 1000.0
    min_bound = scanner_ms
    if moss_ms is not None:
        min_bound = max(min_bound, moss_ms)
    if llm_ms is not None:
        min_bound = max(min_bound, llm_ms)
    total_ms = round(max(elapsed_total, min_bound), 3)

    latency_stats = LatencyStats(
        scanner_ms=scanner_ms,
        moss_ms=moss_ms,
        llm_ms=llm_ms,
        total_ms=total_ms,
    )

    moss_state = MossIngestStatus(
        status=moss_retriever.status,
        loaded=moss_retriever.loaded,
        query_executed=query_executed,
        index_name=moss_retriever.index_name if (query_executed or moss_retriever.loaded) else None,
        result_count=len(moss_matches),
    )

    # Step 6: Privacy-First Audit Logging (never persists raw hostile input or raw LLM prompts)
    try:
        await audit_service.record_event(
            request_id=request_id,
            source_type=request.source_type,
            content_hash=gateway_ctx.content_hash,
            decision=decision,
            risk_score=risk_score,
            findings=findings,
            matched_policy_ids=matched_policy_ids,
            latency=latency_stats,
            sanitized_content=sanitized_content,
            llm_status=llm_state,
        )
    except AuditStorageError:
        # Audit is observability only. A persistence outage must never alter the
        # already-computed security decision or approved context.
        logger.warning(
            "Audit persistence unavailable; preserving security decision request_id=%s decision=%s",
            request_id,
            decision.value,
        )

    return IngestResponse(
        request_id=request_id,
        decision=decision,
        risk_score=risk_score,
        confidence=confidence,
        detected_threats=findings,
        matched_policy_ids=matched_policy_ids,
        sanitized_content=sanitized_content,
        agent_context=agent_context,
        moss=moss_state,
        llm=llm_state,
        latency=latency_stats,
    )
