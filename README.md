# ContextShield Security Gateway

ContextShield is a real-time security gateway that validates untrusted external context before it reaches an AI agent.

ContextShield uses **Google Gemini** (`gemini-3.6-flash`) as its contextual LLM evaluator for genuinely ambiguous cases, combined with a deterministic threat scanner and **Moss Local Runtime** policy retrieval.

## Architecture

```mermaid
flowchart TD
    Raw[Untrusted External Context] --> SG[Schema Gateway: Dual-Buffer & Hash]
    SG --> Scanner[Deterministic Threat Scanner]
    SG --> Moss[Moss Local Runtime Policy Retrieval]
    Scanner & Moss --> RE[Risk Engine: Precedence Hierarchy]
    
    RE --> Obvious{Obvious Decision?<br/>CRITICAL / Strong Aligned /<br/>Clearly SAFE / Clean SANITIZE}
    Obvious -- Yes --> Final[Return Deterministic Decision<br/>LLM NOT Called<br/>llm_ms = null]
    
    Obvious -- No: Ambiguous --> GemCheck{GEMINI_API_KEY<br/>Configured?}
    GemCheck -- No --> GemNotConf[Fail-Secure to REVIEW<br/>status: not_configured<br/>llm_ms = null]
    GemCheck -- Yes --> GemEval[GeminiRiskEvaluator<br/>google-genai SDK<br/>JSON Schema: LLMRiskEvaluation<br/>Target: 800ms | Hard: 1500ms]
    
    GemEval --> TimeoutErr{Timeout / Rate Limited /<br/>Schema Error / Unavailable?}
    TimeoutErr -- Error/Timeout --> ErrFailSec[Fail-Secure<br/>status: timeout / rate_limited / schema_error<br/>Ambiguous -> REVIEW<br/>High-risk -> BLOCK]
    
    TimeoutErr -- Success --> AuthorityCheck{Authority Floor Validation &<br/>Policy Hallucination Filter}
    AuthorityCheck --> Deliver[Final Decision & Ingest Response<br/>total_ms >= llm_ms]
```

## Security Authority Hierarchy
1. **Deterministic CRITICAL**: Absolute priority $\rightarrow$ `BLOCK` (LLM is never called).
2. **Deterministic + Moss Evidence**: High-confidence policy violations $\rightarrow$ `BLOCK`.
3. **Clearly SAFE Content**: Clean ordinary content $\rightarrow$ `SAFE` (LLM is not called).
4. **Ambiguous Sensitive Operations**: Invocations such as bulk customer data exports or database dumps $\rightarrow$ Minimum `REVIEW`. The LLM may never invent authorization or downgrade to `SAFE`.
5. **Fail-Secure Defaults**: Any timeout, quota exhaustion (`rate_limited`), model unavailability, or unconfigured state fails secure to `REVIEW` (or `BLOCK`), ensuring `agent_context` is `null`.

## Configuration

Configure environment variables in `.env` (see `.env.example`):

```env
# Moss Configuration
MOSS_PROJECT_ID=your_project_id
MOSS_PROJECT_KEY=your_project_key
MOSS_INDEX_NAME=contextshield-security

# Contextual LLM Risk Evaluator (Gemini)
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-3.6-flash
LLM_TARGET_LATENCY_MS=800
LLM_HARD_TIMEOUT_MS=1500
```

## Running Tests

```bash
# Run complete test suite (71 tests)
python -m pytest -v

# Run live Gemini integration test
python -m pytest -m gemini_integration -v

# Run end-to-end live verification script
python scripts/verify_gemini_integration.py
```
