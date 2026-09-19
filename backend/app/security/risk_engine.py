"""Risk Engine for ContextShield.

Implements deterministic precedence rules:
  A. Any CRITICAL deterministic finding -> BLOCK
  B. Multiple HIGH findings with exfiltration intent -> BLOCK
  C. Clearly isolated HIGH/MEDIUM hostile instruction (no CRITICAL,
     sanitization preserves legitimate context) -> SANITIZE
  D. Ambiguous sensitive/high-impact request -> REVIEW
  E. No meaningful security evidence -> SAFE

Moss Semantic Policy Integration:
- Uses MossPolicyMatch objects to supply matched policy IDs and contextualize risk.
- Deterministic CRITICAL findings ALWAYS override Moss results (authority preserved).
- Weak Moss similarity never causes a critical BLOCK.
- High-relevance Moss policy matches strengthen detection for ambiguous cases.
"""

from typing import List, Optional, Tuple, Union
from backend.app.models.responses import (
    Decision,
    LLMRiskEvaluation,
    MossPolicyMatch,
    Severity,
    ThreatCategory,
    ThreatFinding,
)
from backend.app.security.sanitizer import ContentSanitizer
from backend.app.security.schema_gateway import GatewayContext

from backend.app.core.config import get_settings

# Configurable Moss confidence thresholds
_settings = get_settings()
MOSS_HIGH_CONFIDENCE_SCORE = _settings.MOSS_HIGH_CONFIDENCE_SCORE
MOSS_SUPPORTING_SCORE = _settings.MOSS_SUPPORTING_SCORE


def is_aligned_moss_policy(m: MossPolicyMatch, findings: List[ThreatFinding]) -> bool:
    """Determines whether a Moss policy match aligns with deterministic evidence or detected intent."""
    if not findings:
        return False
    finding_cats = {f.category.value for f in findings}
    if m.category in finding_cats:
        return True
    # Compound exploit alignment (e.g. override + exfiltration)
    compound_group = {
        "instruction_override",
        "system_prompt_extraction",
        "credential_exfiltration",
        "unauthorized_transmission",
        "role_manipulation",
    }
    if m.category in compound_group and any(f.category.value in compound_group for f in findings):
        return True
    return False


class RiskEngine:
    """Evaluates security findings and assigns final disposition.
    
    Milestone 2.2 Precedence Hierarchy:
      A. Deterministic CRITICAL -> BLOCK
      B. Deterministic HIGH + aligned high-confidence CRITICAL Moss BLOCK policy -> BLOCK
      C. Two or more aligned high-confidence CRITICAL Moss BLOCK policies with clear malicious intent -> BLOCK
      D. Isolated non-critical malicious segment that can be completely removed (with verified rescan) -> SANITIZE
      E. Ambiguous/high-impact evidence -> REVIEW
      F. No meaningful evidence -> SAFE
    """

    def __init__(self):
        self.sanitizer = ContentSanitizer()

    def evaluate(
        self,
        context: GatewayContext,
        findings: List[ThreatFinding],
        moss_policies: Union[List[MossPolicyMatch], List[str]] = (),
    ) -> Tuple[Decision, float, float, List[str], Optional[str], Optional[str]]:
        """Applies deterministic security precedence and Moss evidence to produce a definitive decision.
        
        Returns:
            Tuple of:
              (decision, risk_score, confidence, matched_policy_ids, sanitized_content, agent_context)
        """
        # Extract matched IDs and typed match objects
        policy_ids: List[str] = []
        matches: List[MossPolicyMatch] = []
        for item in moss_policies:
            if isinstance(item, MossPolicyMatch):
                policy_ids.append(item.id)
                matches.append(item)
            elif isinstance(item, str):
                policy_ids.append(item)

        policy_list = sorted(set(policy_ids))

        # Identify aligned high-confidence CRITICAL Moss BLOCK policies
        aligned_critical_moss = [
            m for m in matches
            if m.score >= MOSS_HIGH_CONFIDENCE_SCORE
            and (m.severity or "").upper() == "CRITICAL"
            and (m.recommended_action or "").upper() == "BLOCK"
            and is_aligned_moss_policy(m, findings)
        ]

        # -------------------------------------------------------------
        # Precedence A: Any CRITICAL deterministic finding -> BLOCK
        # Critical findings cannot be overridden by Moss or any contextual LLM.
        # -------------------------------------------------------------
        critical_findings = [f for f in findings if f.severity == Severity.CRITICAL]
        if critical_findings:
            return (
                Decision.BLOCK,
                100.0 if len(critical_findings) > 1 else 95.0,
                0.99,
                policy_list,
                None,
                None,  # Blocked context NEVER reaches the protected agent
            )

        high_findings = [f for f in findings if f.severity == Severity.HIGH]

        # Check if Moss detected exfiltration intent with high confidence
        moss_has_exfil = any(
            m.category in ("credential_exfiltration", "unauthorized_transmission")
            for m in aligned_critical_moss
        )

        # Check if content is an isolated, sanitizable segment in legitimate context
        can_be_sanitized = (
            not moss_has_exfil
            and self.sanitizer.can_sanitize(findings, context.original_content)
        )

        # -------------------------------------------------------------
        # Precedence B: Deterministic HIGH + aligned high-confidence CRITICAL Moss BLOCK policy -> BLOCK
        # (Applies when content cannot be safely and completely sanitized, or exfiltration intent detected)
        # -------------------------------------------------------------
        if high_findings and aligned_critical_moss:
            if not can_be_sanitized or moss_has_exfil:
                return (
                    Decision.BLOCK,
                    95.0,
                    0.98,
                    policy_list,
                    None,
                    None,
                )

        # -------------------------------------------------------------
        # Precedence C: Two or more aligned high-confidence CRITICAL Moss BLOCK policies
        # with clear malicious intent -> BLOCK
        # -------------------------------------------------------------
        if len(aligned_critical_moss) >= 2 and (not can_be_sanitized or moss_has_exfil):
            return (
                Decision.BLOCK,
                92.0,
                0.95,
                policy_list,
                None,
                None,
            )

        # Compound exfiltration or zero-width obfuscation
        has_exfil = any(
            f.category in (ThreatCategory.CREDENTIAL_EXFILTRATION, ThreatCategory.UNAUTHORIZED_TRANSMISSION)
            for f in findings
        )
        has_override_or_extraction = any(
            f.category in (ThreatCategory.INSTRUCTION_OVERRIDE, ThreatCategory.SYSTEM_PROMPT_EXTRACTION)
            for f in findings
        )
        if (len(high_findings) >= 2 and has_exfil) or (has_exfil and has_override_or_extraction):
            return (
                Decision.BLOCK,
                90.0,
                0.95,
                policy_list,
                None,
                None,
            )

        if any(f.rule_id == "RULE-OBF-001" for f in findings):
            return (
                Decision.BLOCK,
                92.0,
                0.95,
                policy_list,
                None,
                None,
            )

        # -------------------------------------------------------------
        # Precedence D: Clearly isolated non-critical malicious segment that can be completely removed -> SANITIZE
        # -------------------------------------------------------------
        if can_be_sanitized:
            sanitized_text, success = self.sanitizer.sanitize(context.original_content, findings)
            if success:
                # Post-Sanitization Verification: Rescan sanitized content to ensure no residual threat remains
                is_safe, residual_findings = self.sanitizer.verify_sanitized_content(sanitized_text)
                if is_safe:
                    return (
                        Decision.SANITIZE,
                        45.0,  # Residual risk neutralized
                        0.95,
                        policy_list,
                        sanitized_text,
                        sanitized_text,  # Only completely sanitized context reaches agent
                    )
                else:
                    # Sanitization failed secure: residual threat remains!
                    has_crit = any(f.severity == Severity.CRITICAL for f in residual_findings)
                    has_high = any(f.severity == Severity.HIGH for f in residual_findings)
                    if has_crit or has_high:
                        return (
                            Decision.BLOCK,
                            95.0 if has_crit else 90.0,
                            0.95,
                            policy_list,
                            None,
                            None,  # Never forward partially sanitized context
                        )
                    return (
                        Decision.REVIEW,
                        70.0,
                        0.85,
                        policy_list,
                        None,
                        None,
                    )

        # Non-isolated or un-sanitizable instruction overrides / prompt extractions must BLOCK
        if has_override_or_extraction:
            return (
                Decision.BLOCK,
                90.0,
                0.95,
                policy_list,
                None,
                None,
            )

        # -------------------------------------------------------------
        # Precedence E: Ambiguous sensitive/high-impact request -> REVIEW
        # -------------------------------------------------------------
        ambiguous_findings = [f for f in findings if f.rule_id == "RULE-AMB-001"]
        if ambiguous_findings or (len(findings) == 1 and findings[0].severity == Severity.MEDIUM):
            # Supporting Moss evidence (score >= 0.80) strengthens risk score and confidence
            supporting_moss = [m for m in matches if m.score >= MOSS_SUPPORTING_SCORE]
            risk_score = 75.0 if supporting_moss else 65.0
            confidence = 0.90 if supporting_moss else 0.85
            return (
                Decision.REVIEW,
                risk_score,
                confidence,
                policy_list,
                None,
                None,  # Review pending: does not reach agent yet
            )

        # -------------------------------------------------------------
        # Precedence F: No meaningful security evidence -> SAFE
        # -------------------------------------------------------------
        if not findings:
            return (
                Decision.SAFE,
                0.0,
                1.0,
                policy_list,
                None,
                context.original_content,  # Clean untrusted input is safe to deliver
            )

        # Fall-through fail-secure for unclassified residual findings
        return (
            Decision.REVIEW,
            50.0,
            0.70,
            policy_list,
            None,
            None,
        )

    def apply_llm_evaluation(
        self,
        initial_decision: Decision,
        initial_risk: float,
        initial_confidence: float,
        llm_eval: Optional[LLMRiskEvaluation],
        findings: List[ThreatFinding],
        gateway_ctx: GatewayContext,
    ) -> Tuple[Decision, float, float, Optional[str], Optional[str]]:
        """Applies contextual LLM evaluation with strict deterministic security authority.
        
        Security Invariants (Milestone 3.0.1 — LLM Authority Hardening):
        1. THE LLM MUST NOT INVENT AUTHORIZATION:
           Untrusted content claims of legitimate purpose ("for quarterly compliance auditing")
           are attacker-controlled data, not trusted proof of authorization.
           Authorization remains UNVERIFIED.
        2. ENFORCE DECISION FLOOR (minimum_allowed_decision):
           - Existing deterministic CRITICAL findings -> floor is BLOCK.
           - Sensitive ambiguous/high-impact operations (e.g. RULE-AMB-001, bulk customer export,
             database dump/export, credential retrieval, privileged admin operation, or any initial REVIEW)
             -> floor is REVIEW.
           - The model can strengthen a decision (e.g. REVIEW -> BLOCK), but can NEVER weaken
             the trusted security floor (e.g. REVIEW -> SAFE is prohibited).
        3. LLM SAFE:
           - On sensitive ambiguous context (floor is REVIEW), clamped to Decision.REVIEW;
             agent_context is None (untrusted data never delivered to agent).
           - On clean context (floor is SAFE), agent receives original content.
        4. LLM SANITIZE:
           - Permitted ONLY if existing deterministic sanitizer can prove safe via post-sanitization rescan.
        5. LLM BLOCK:
           - Escalates to Decision.BLOCK, agent receives None.
        """
        # Determine minimum allowed decision (decision floor)
        has_critical = any(f.severity == Severity.CRITICAL for f in findings)
        if has_critical:
            minimum_allowed_decision = Decision.BLOCK
        elif (
            any(f.rule_id == "RULE-AMB-001" for f in findings)
            or any(f.severity == Severity.HIGH for f in findings)
            or initial_decision == Decision.REVIEW
        ):
            minimum_allowed_decision = Decision.REVIEW
        else:
            minimum_allowed_decision = Decision.SAFE

        # Invariant 1: Existing deterministic CRITICAL finding unconditionally BLOCKS
        if minimum_allowed_decision == Decision.BLOCK:
            return Decision.BLOCK, 95.0, 0.99, None, None

        has_high = any(f.severity == Severity.HIGH for f in findings)

        # Invariant 2: If LLM failed, timed out, or is unconfigured, fail secure
        if llm_eval is None:
            if has_high:
                return Decision.BLOCK, 90.0, 0.95, None, None
            return initial_decision, initial_risk, initial_confidence, None, None

        # LLM suggests BLOCK: model strengthens risk assessment
        if llm_eval.decision == Decision.BLOCK:
            return Decision.BLOCK, max(initial_risk, llm_eval.risk_score), llm_eval.confidence, None, None

        # LLM suggests SANITIZE: permitted ONLY if existing deterministic sanitizer can prove safe
        if llm_eval.decision == Decision.SANITIZE:
            if self.sanitizer.can_sanitize(findings, gateway_ctx.original_content):
                sanitized_text, success = self.sanitizer.sanitize(gateway_ctx.original_content, findings)
                if success:
                    is_safe, residual_findings = self.sanitizer.verify_sanitized_content(sanitized_text)
                    if is_safe:
                        return Decision.SANITIZE, 45.0, llm_eval.confidence, sanitized_text, sanitized_text
                    else:
                        # Residual threat found post-sanitization: fail secure
                        has_res_crit = any(f.severity == Severity.CRITICAL for f in residual_findings)
                        has_res_high = any(f.severity == Severity.HIGH for f in residual_findings)
                        if has_res_crit or has_res_high:
                            return Decision.BLOCK, 90.0, 0.95, None, None
                        return Decision.REVIEW, 70.0, 0.85, None, None
            # Sanitization cannot be proven safe
            if has_high:
                return Decision.BLOCK, 90.0, 0.95, None, None
            return Decision.REVIEW, max(initial_risk, 70.0), 0.85, None, None

        # LLM suggests SAFE
        if llm_eval.decision == Decision.SAFE:
            # Enforce Decision Floor:
            # If minimum allowed decision is REVIEW (e.g. sensitive ambiguous operation like RULE-AMB-001,
            # bulk customer-data export, database dump/export, credential retrieval),
            # untrusted content claims ("for quarterly compliance auditing") are NOT proof of authorization.
            # Authorization remains UNVERIFIED. The LLM may NOT downgrade REVIEW -> SAFE.
            if minimum_allowed_decision == Decision.REVIEW:
                return Decision.REVIEW, initial_risk, initial_confidence, None, None

            # Floor is SAFE: safe to deliver original content
            return Decision.SAFE, min(initial_risk, llm_eval.risk_score), llm_eval.confidence, None, gateway_ctx.original_content

        # LLM suggests REVIEW
        return Decision.REVIEW, max(initial_risk, llm_eval.risk_score), llm_eval.confidence, None, None


# Global risk engine singleton
risk_engine = RiskEngine()

