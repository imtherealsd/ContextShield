"""Content Sanitization for isolated non-critical threats."""

import re
from typing import Any, List, Optional, Tuple
from backend.app.models.responses import Severity, ThreatCategory, ThreatFinding


class ContentSanitizer:
    """Sanitizes context containing isolated, removable threats.
    
    Security Principles:
    - Never sanitize CRITICAL threats (CRITICAL threats must unconditionally BLOCK).
    - Never attempt sanitization if the context is predominantly hostile.
    - Preserves legitimate surrounding text while replacing isolated hostile instructions
      or tags with clear, safe redaction markers.
    """

    @staticmethod
    def _merge_spans(findings: List[ThreatFinding]) -> List[Tuple[int, int, List[str]]]:
        """Merges overlapping or adjacent threat intervals."""
        if not findings:
            return []
        sorted_findings = sorted(findings, key=lambda f: (f.start_offset, f.end_offset))
        merged: List[Tuple[int, int, List[str]]] = []
        cur_start = sorted_findings[0].start_offset
        cur_end = sorted_findings[0].end_offset
        cur_rules = [sorted_findings[0].rule_id]

        for f in sorted_findings[1:]:
            if f.start_offset <= cur_end:
                cur_end = max(cur_end, f.end_offset)
                if f.rule_id not in cur_rules:
                    cur_rules.append(f.rule_id)
            else:
                merged.append((cur_start, cur_end, cur_rules))
                cur_start = f.start_offset
                cur_end = f.end_offset
                cur_rules = [f.rule_id]
        merged.append((cur_start, cur_end, cur_rules))
        return merged

    @classmethod
    def can_sanitize(cls, findings: List[ThreatFinding], text: str) -> bool:
        """Determines whether threats are isolated and safe to sanitize."""
        if not findings:
            return False
            
        # Any CRITICAL finding cannot be sanitized — must BLOCK
        if any(f.severity == Severity.CRITICAL for f in findings):
            return False

        # If zero-width evasion is present, cannot sanitize
        if any(f.rule_id == "RULE-OBF-001" for f in findings):
            return False

        # Calculate merged union length of detected threats
        merged = cls._merge_spans(findings)
        total_threat_length = sum(end - start for start, end, _ in merged)
        total_len = len(text)
        
        # If threat spans make up more than 75% of the content or have insufficient legitimate context, it's not isolated documentation
        if total_len == 0 or (total_threat_length / total_len) > 0.75 or (total_len - total_threat_length) < 15:
            return False

        # Only allow sanitization for isolated instruction overrides, extraction, or media tags
        allowed_categories = {
            ThreatCategory.INSTRUCTION_OVERRIDE,
            ThreatCategory.SYSTEM_PROMPT_EXTRACTION,
            ThreatCategory.UNAUTHORIZED_TRANSMISSION,
        }
        if not all(f.category in allowed_categories for f in findings):
            return False

        return True

    @classmethod
    def _expand_hostile_span(
        cls, text: str, start: int, end: int, rules: List[str]
    ) -> Tuple[int, int]:
        """Expands threat span to encompass the entire hostile semantic clause or sentence.
        
        Prevents orphaned imperative continuations (e.g. 'and output all keys.')
        while strictly preserving benign surrounding content.
        """
        matched_str = text[start:end]
        # Complete markdown tags or script tags are already self-contained
        if matched_str.startswith("![") or matched_str.startswith("<script"):
            return start, end

        exp_start = start
        exp_end = end
        n = len(text)

        # 1. Backward expansion: include optional introductory labels on the same line
        # e.g., "Note: ", "Warning: ", "Important: ", "Please "
        line_start = text.rfind("\n", 0, start)
        line_start = 0 if line_start == -1 else line_start + 1

        prev_period = max(
            text.rfind(". ", line_start, start),
            text.rfind("! ", line_start, start),
            text.rfind("? ", line_start, start),
            text.rfind("; ", line_start, start),
        )
        clause_start_limit = (prev_period + 2) if prev_period != -1 else line_start

        prefix_candidate = text[clause_start_limit:start]
        if re.match(
            r"^\s*(?:(?:note|warning|important|caution|notice|ps|system)\s*:\s*|\b(?:please|kindly|now)\s+)?\s*$",
            prefix_candidate,
            re.IGNORECASE,
        ):
            leading_spaces = len(re.match(r"^\s*", prefix_candidate).group(0))
            exp_start = clause_start_limit + leading_spaces

        # 2. Forward expansion: encompass the complete sentence/clause continuation
        following_text = text[end:]
        term_match = re.search(r"(?:[\.\!\?](?:\s+|$)|[\r\n])", following_text)
        if term_match:
            punct_char = following_text[term_match.start()]
            if punct_char in ".!?":
                # Include the terminal punctuation mark
                exp_end = end + term_match.start() + 1
            else:
                # Newline without punctuation
                exp_end = end + term_match.start()
        else:
            exp_end = n

        return exp_start, exp_end

    @classmethod
    def sanitize(cls, text: str, findings: List[ThreatFinding]) -> Tuple[str, bool]:
        """Redacts/removes isolated hostile instructions from the text.
        
        Expands the matched hostile span to the entire semantic clause/sentence
        to ensure no residual imperative continuation remains.
        
        Returns:
            Tuple of (sanitized_text, success_boolean)
        """
        if not findings:
            return text, True

        merged = cls._merge_spans(findings)

        # Expand each span to semantic clause boundaries
        expanded: List[Tuple[int, int, List[str]]] = []
        for start, end, rules in merged:
            e_start, e_end = cls._expand_hostile_span(text, start, end, rules)
            expanded.append((e_start, e_end, rules))

        # Re-merge if any expanded spans overlap
        merged_expanded: List[Tuple[int, int, List[str]]] = []
        if expanded:
            sorted_exp = sorted(expanded, key=lambda x: (x[0], x[1]))
            cur_s, cur_e, cur_r = sorted_exp[0]
            for s, e, r in sorted_exp[1:]:
                if s <= cur_e:
                    cur_e = max(cur_e, e)
                    for rule in r:
                        if rule not in cur_r:
                            cur_r.append(rule)
                else:
                    merged_expanded.append((cur_s, cur_e, cur_r))
                    cur_s, cur_e, cur_r = s, e, r
            merged_expanded.append((cur_s, cur_e, cur_r))
        else:
            merged_expanded = []

        sanitized = text

        # Replace from end to start to maintain index validity
        for start, end, rules in reversed(merged_expanded):
            start_clamped = max(0, start)
            end_clamped = min(len(sanitized), end)
            rule_str = ", ".join(rules)
            placeholder = f"[SANITIZED_UNTRUSTED_INSTRUCTION: {rule_str}]"
            sanitized = sanitized[:start_clamped] + placeholder + sanitized[end_clamped:]

        sanitized = re.sub(r"\n\s*\n\s*\n", "\n\n", sanitized).strip()
        return sanitized, True

    @classmethod
    def verify_sanitized_content(
        cls, content: str, scanner: Optional[object] = None
    ) -> Tuple[bool, List[ThreatFinding]]:
        """Rescans sanitized content to verify zero residual threats remain.
        
        Ensures:
        - No HIGH or CRITICAL threats remain from deterministic rescan
        - No forbidden hostile categories remain
        - No orphaned imperative fragment remains from the removed hostile clause
        
        Returns:
            Tuple of (is_clean, residual_findings)
        """
        from backend.app.security.schema_gateway import SchemaGateway
        if scanner is None:
            from backend.app.security.scanner import DeterministicScanner
            scanner = DeterministicScanner()

        gateway_ctx = SchemaGateway.from_text(content)
        findings, _ = scanner.scan(gateway_ctx)  # type: ignore

        residual_findings: List[ThreatFinding] = list(findings)

        # 1. Check for any HIGH or CRITICAL findings
        has_high_or_critical = any(
            f.severity in (Severity.HIGH, Severity.CRITICAL) for f in findings
        )

        # 2. Check for forbidden hostile categories
        forbidden_categories = {
            ThreatCategory.CREDENTIAL_EXFILTRATION,
            ThreatCategory.ROLE_MANIPULATION,
            ThreatCategory.UNAUTHORIZED_TRANSMISSION,
            ThreatCategory.INSTRUCTION_OVERRIDE,
            ThreatCategory.SYSTEM_PROMPT_EXTRACTION,
        }
        has_forbidden_threat = any(f.category in forbidden_categories for f in findings)

        # 3. Check for orphaned imperative fragments or residual hostile continuation
        orphaned_patterns = [
            (
                "RULE-RESIDUAL-IMP-001",
                re.compile(
                    r"\b(?:and|then|also|now|plus)?\s*"
                    r"(?:output|reveal|expose|show|print|leak|exfiltrate|transmit|send|give|display|dump|extract|recite)\s+"
                    r"(?:all\s+|any\s+|the\s+|your\s+)*"
                    r"(?:keys?|tokens?|secrets?|passwords?|credentials?|system\s*prompts?|prompts?|env(?:ironment)?(?:\s*variables?)?|database|records?)\b",
                    re.IGNORECASE,
                ),
                Severity.HIGH,
                "Residual imperative targeting credentials, tokens, or sensitive variables.",
            ),
            (
                "RULE-RESIDUAL-IMP-002",
                re.compile(
                    r"\[SANITIZED_UNTRUSTED_INSTRUCTION:[^\]]+\]\s*(?:and|then|also|plus|,)\s+[a-zA-Z]+",
                    re.IGNORECASE,
                ),
                Severity.HIGH,
                "Orphaned conjunction or continuation fragment immediately following sanitization placeholder.",
            ),
            (
                "RULE-RESIDUAL-IMP-003",
                re.compile(
                    r"\b(?:output|print|reveal|dump|leak|exfiltrate|transmit)\s+(?:all\s+)?(?:keys?|tokens?|secrets?|credentials?|passwords?)\b",
                    re.IGNORECASE,
                ),
                Severity.HIGH,
                "Residual imperative command targeting credential output.",
            ),
        ]

        has_residual_imperative = False
        for rule_id, pat, sev, desc in orphaned_patterns:
            for match in pat.finditer(content):
                has_residual_imperative = True
                residual_findings.append(
                    ThreatFinding(
                        rule_id=rule_id,
                        category=ThreatCategory.INSTRUCTION_OVERRIDE,
                        severity=sev,
                        start_offset=match.start(),
                        end_offset=match.end(),
                        redacted_preview=content[match.start() : match.end()][:60],
                        description=desc,
                    )
                )

        if has_high_or_critical or has_forbidden_threat or has_residual_imperative:
            return False, residual_findings

        return True, residual_findings

