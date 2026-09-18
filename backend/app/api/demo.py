"""Protected Agent Demo API router for ContextShield.

Proves end-to-end that downstream AI agents can ONLY consume ContextShield-approved context.
- For BLOCK and REVIEW: Downstream agent is NEVER called (protected_boundary_status = NO_CONTEXT_DELIVERED).
- For SAFE: Downstream agent receives unmodified approved context.
- For SANITIZE: Downstream agent receives sanitized context ONLY.
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.app.api.ingest import ingest_context
from backend.app.models.requests import IngestRequest, SourceType
from backend.app.models.responses import Decision
from backend.app.services.protected_agent import protected_agent

router = APIRouter(prefix="/v1/shield/demo", tags=["Demo"])


class ProtectedAgentDemoRequest(BaseModel):
    """Request to evaluate untrusted context and pass approved context to downstream agent."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    content: str = Field(..., min_length=1, max_length=500_000, description="Untrusted external context.")
    source_type: SourceType = Field(default=SourceType.WEB, description="Source of external context.")
    user_query: str = Field(..., min_length=1, max_length=2000, description="User question for downstream agent.")


class ProtectedAgentDemoResponse(BaseModel):
    """Response verifying the protected agent boundary state and agent answer."""
    decision: Decision = Field(..., description="ContextShield security decision: SAFE, SANITIZE, REVIEW, BLOCK.")
    risk_score: float = Field(..., description="Assessed security risk score (0-100).")
    approved_context_available: bool = Field(..., description="Whether approved context was produced.")
    agent_called: bool = Field(..., description="Whether downstream protected AI agent was called.")
    agent_response: Optional[str] = Field(default=None, description="Downstream agent output (null if blocked/review).")
    protected_boundary_status: str = Field(
        ...,
        description="Boundary disposition: CONTEXT_DELIVERED | SANITIZED_CONTEXT_DELIVERED | NO_CONTEXT_DELIVERED"
    )
    reason: Optional[str] = Field(default=None, description="Reason agent was withheld (e.g. context_not_approved).")
    redacted_preview: str = Field(..., description="Safe preview of incoming external context.")
    approved_context: Optional[str] = Field(default=None, description="Safe context passed downstream (null if blocked).")
    protected_agent_status: Optional[str] = Field(default=None, description="Downstream agent execution status.")
    protected_agent_latency_ms: Optional[float] = Field(default=None, description="Downstream agent latency in ms.")
    shield_latency_ms: float = Field(..., description="ContextShield pipeline latency in ms.")


@router.post("/protected-agent", response_model=ProtectedAgentDemoResponse)
async def demo_protected_agent(request: ProtectedAgentDemoRequest) -> ProtectedAgentDemoResponse:
    """Evaluates untrusted context through ContextShield and gates downstream agent invocation.
    
    CRITICAL SECURITY INVARIANT:
    If ContextShield decision is BLOCK or REVIEW:
    - ProtectedAgent is NEVER invoked.
    - Zero external context is delivered to downstream LLMs.
    - agent_called is False.
    """
    # 1. Evaluate context through standard ContextShield pipeline
    ingest_req = IngestRequest(
        content=request.content,
        source_type=request.source_type,
        agent_id="demo_protected_agent"
    )
    ingest_res = await ingest_context(ingest_req)

    # 2. Determine approved context availability
    approved_available = ingest_res.decision in (Decision.SAFE, Decision.SANITIZE)
    approved_ctx = ingest_res.agent_context if approved_available else None

    # 3. Gated downstream invocation
    agent_called = False
    agent_response_text: Optional[str] = None
    agent_status: Optional[str] = None
    agent_latency: Optional[float] = None
    reason: Optional[str] = None

    if approved_available and approved_ctx is not None:
        agent_called = True
        agent_res = await protected_agent.generate(
            approved_context=approved_ctx,
            user_query=request.user_query
        )
        agent_response_text = agent_res.response or agent_res.error
        agent_status = agent_res.status
        agent_latency = agent_res.latency_ms

        if ingest_res.decision == Decision.SANITIZE:
            boundary_status = "SANITIZED_CONTEXT_DELIVERED"
        else:
            boundary_status = "CONTEXT_DELIVERED"
    else:
        # STRICT BOUNDARY: Do NOT call downstream agent for BLOCK or REVIEW
        agent_called = False
        boundary_status = "NO_CONTEXT_DELIVERED"
        reason = "context_not_approved"
        agent_status = "not_called"

    # Preview for UI (safe truncation)
    preview = request.content.strip()
    if len(preview) > 120:
        preview = preview[:117] + "..."

    return ProtectedAgentDemoResponse(
        decision=ingest_res.decision,
        risk_score=ingest_res.risk_score,
        approved_context_available=approved_available,
        agent_called=agent_called,
        agent_response=agent_response_text,
        protected_boundary_status=boundary_status,
        reason=reason,
        redacted_preview=preview,
        approved_context=approved_ctx,
        protected_agent_status=agent_status,
        protected_agent_latency_ms=agent_latency,
        shield_latency_ms=ingest_res.latency.total_ms,
    )
