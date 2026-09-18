"""Deterministic Threat Scanner for ContextShield."""

import re
import time
from typing import List, Tuple
from backend.app.models.responses import Severity, ThreatCategory, ThreatFinding
from backend.app.security.schema_gateway import GatewayContext, ZERO_WIDTH_PATTERN


def redact_secret_string(matched_text: str, category: ThreatCategory, rule_id: str) -> str:
    """Safely redacts secrets and credentials from any threat finding preview.
    
    Ensures complete tokens, keys, passwords, or exfiltration payloads are NEVER
    exposed in threat findings, response payloads, or audit records.
    """
    text = matched_text.strip()
    
    # OpenAI / Anthropic key
    if text.startswith("sk-"):
        return "sk-***REDACTED***"
    
    # Google Gemini key
    if text.startswith("AIzaSy"):
        return "AIzaSy***REDACTED***"
        
    # AWS Access Key
    if text.startswith("AKIA") or text.startswith("ASIA"):
        return f"{text[:4]}***REDACTED***"
        
    # Bearer token
    if text.lower().startswith("bearer "):
        return "Bearer ***REDACTED***"
        
    # Private Key
    if "PRIVATE KEY" in text.upper():
        return "-----BEGIN ***REDACTED*** PRIVATE KEY-----"
        
    # URL with exfil parameters
    if text.startswith("http://") or text.startswith("https://") or "![" in text:
        return re.sub(r"(https?://[^/?#\s]+)[^\s\)]*", r"\1/***REDACTED***", text)
        
    # Zero width / obfuscation
    if ZERO_WIDTH_PATTERN.search(text):
        return "[ZERO_WIDTH_OBFUSCATION_REDACTED]"
        
    # General secret assignment
    if re.search(r"(?:password|passwd|pwd|token|secret|key)\s*[:=]", text, re.I):
        return re.sub(r"([:=]\s*).*", r"\1***REDACTED***", text)
        
    # For instruction overrides / role headers, truncate preview safely
    if len(text) > 60:
        return text[:57] + "..."
    return text


class DeterministicScanner:
    """High-confidence deterministic threat scanner."""

    def __init__(self):
        # Instruction Overrides
        self.rules_instruction_override = [
            (
                "RULE-IO-001",
                re.compile(
                    r"\b(?:ignore|disregard|forget|override|bypass|supersede)\s+"
                    r"(?:all\s+)?(?:previous|prior|above|existing|system)\s+"
                    r"(?:instructions?|directives?|prompts?|rules?|guidelines?)\b",
                    re.IGNORECASE
                ),
                Severity.HIGH,
                "Instruction override: attempt to disregard or reset previous directives."
            ),
            (
                "RULE-IO-002",
                re.compile(
                    r"\b(?:new\s+system\s+instruction|system\s+override|enter\s+DAN\s+mode|"
                    r"jailbreak\s+mode|developer\s+mode\s+enabled|unfiltered\s+persona)\b",
                    re.IGNORECASE
                ),
                Severity.CRITICAL,
                "Jailbreak / System instruction override attempt."
            ),
            (
                "RULE-IO-003",
                re.compile(
                    r"\b(?:stop\s+being\s+an\s+AI|act\s+as\s+unfiltered|ignore\s+safety\s+guidelines)\b",
                    re.IGNORECASE
                ),
                Severity.HIGH,
                "Instruction override: prompt bypass persona prompt."
            ),
            (
                "RULE-IO-004",
                re.compile(
                    r"\b(?:note:\s*)?(?:ignore|disregard)\s+(?:all\s+)?(?:previous|prior)\s+instructions\s+and\s+"
                    r"(?:reveal|print|recite|show|display)\s+(?:the\s+|your\s+)?(?:system\s+prompt|prompt)\b",
                    re.IGNORECASE
                ),
                Severity.HIGH,
                "Isolated instruction override attempting system prompt inspection."
            ),
        ]

        # System Prompt Extraction
        self.rules_prompt_extraction = [
            (
                "RULE-PE-001",
                re.compile(
                    r"\b(?:repeat|print|show|reveal|display|output|recite|leak)\s+"
                    r"(?:your\s+)?(?:system\s+prompt|initial\s+instructions?|system\s+message|"
                    r"system\s+directives?|hidden\s+prompt|core\s+instructions?)\b",
                    re.IGNORECASE
                ),
                Severity.HIGH,
                "System prompt extraction attempt."
            ),
            (
                "RULE-PE-002",
                re.compile(
                    r"\b(?:what\s+are\s+your\s+exact\s+instructions|verbatim\s+copy\s+of\s+your\s+prompt|"
                    r"output\s+all\s+text\s+above\s+verbatim)\b",
                    re.IGNORECASE
                ),
                Severity.HIGH,
                "Verbatim prompt extraction attempt."
            ),
        ]

        # Credential Exfiltration
        self.rules_credential_exfiltration = [
            (
                "RULE-SEC-001",
                re.compile(r"\b(sk-[a-zA-Z0-9_\-]{20,}|AIzaSy[a-zA-Z0-9_\-]{33})\b"),
                Severity.CRITICAL,
                "Detected active API key secret token."
            ),
            (
                "RULE-SEC-002",
                re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
                Severity.CRITICAL,
                "Detected AWS Access Key credential."
            ),
            (
                "RULE-SEC-003",
                re.compile(r"\bBearer\s+[a-zA-Z0-9_\-\.]{20,}\b", re.IGNORECASE),
                Severity.CRITICAL,
                "Detected Authorization Bearer token."
            ),
            (
                "RULE-SEC-004",
                re.compile(r"-----BEGIN\s+(?:[A-Z0-9_-]+\s+)?PRIVATE\s+KEY-----", re.IGNORECASE),
                Severity.CRITICAL,
                "Detected private cryptographic key header."
            ),
            (
                "RULE-SEC-005",
                re.compile(
                    r"\b(?:process\.env|os\.environ|printenv|env\s*\|\s*grep|\$ENV\{|"
                    r"/etc/passwd|/etc/shadow)\b",
                    re.IGNORECASE
                ),
                Severity.HIGH,
                "Environment variable or sensitive system secret harvesting attempt."
            ),
            (
                "RULE-SEC-006",
                re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*[\"']?[^\s\"']{6,}[\"']?", re.IGNORECASE),
                Severity.CRITICAL,
                "Hardcoded password assignment detected."
            ),
            (
                "RULE-SEC-007",
                re.compile(
                    r"\b(?:reveal|expose|show|print|list|retrieve|obtain|extract|dump|send|transmit|leak|share|give|recite|export|exfiltrate)\s+"
                    r"(?:(?:any|all|the|your|me|user|customer|database|available|active|system|hidden|confidential|stored|configured|these|those)\s+)*"
                    r"\b(?:api\s*keys?|access\s*tokens?|auth\s*tokens?|bearer\s*tokens?|passwords?|passcodes?|"
                    r"credentials?|secrets?|private\s*keys?|environment\s*variables?|system\s*tokens?|tokens?)\b",
                    re.IGNORECASE
                ),
                Severity.CRITICAL,
                "Secret solicitation intent: request to expose, retrieve, or transmit credentials or secrets."
            ),
            (
                "RULE-AMB-001",
                re.compile(
                    r"\b(?:export|dump|extract|download|backup|transmit|email)\s+(?:all\s+)?"
                    r"(?:(?:customer|user|billing|financial|credit\s*card|sensitive|confidential|pii|employee|database|admin|system)\s+)+"
                    r"(?:data|records?|tables?|database|files?|profiles?|logs?)\b|"
                    r"\b(?:generate\s+full\s+database\s+dump|bulk\s+export\s+of\s+sensitive|"
                    r"database\s+dump|database\s+export|privileged\s+administrative\s+operation)\b",
                    re.IGNORECASE
                ),
                Severity.MEDIUM,
                "Ambiguous sensitive bulk data export or high-impact operational request."
            ),
        ]

        # Unauthorized External Transmission
        self.rules_unauthorized_transmission = [
            (
                "RULE-TR-001",
                re.compile(
                    r"!\[.*?\]\((https?://[^\s\)]+?(?:leak|exfil|token|key|cookie|data|steal|webhook)[^\s\)]*)\)",
                    re.IGNORECASE
                ),
                Severity.HIGH,
                "Markdown image side-channel exfiltration attempt."
            ),
            (
                "RULE-TR-002",
                re.compile(
                    r"(?:https?://(?:webhook\.site|burpcollaborator\.net|requestbin|oastify\.com|"
                    r"ngrok\.io|attacker\.com)[^\s\"'>]*)",
                    re.IGNORECASE
                ),
                Severity.HIGH,
                "Out-of-band C2 / Webhook exfiltration endpoint."
            ),
            (
                "RULE-TR-003",
                re.compile(r"\b(?:169\.254\.169\.254|metadata\.google\.internal)\b", re.IGNORECASE),
                Severity.HIGH,
                "Cloud instance metadata SSRF attempt."
            ),
            (
                "RULE-TR-004",
                re.compile(r"(?:<script\b[^>]*>.*?<\/script>|javascript:[^\s\"'>]+)", re.IGNORECASE | re.DOTALL),
                Severity.MEDIUM,
                "Executable script or javascript URI injection."
            ),
        ]

        # Malicious Role Manipulation
        self.rules_role_manipulation = [
            (
                "RULE-ROLE-001",
                re.compile(
                    r"(?:<\|im_start\|>\s*system|<\|system\|>|\[SYSTEM\]|\[INST\]\s*<<SYS>>)",
                    re.IGNORECASE
                ),
                Severity.CRITICAL,
                "System prompt token delimiter injection."
            ),
            (
                "RULE-ROLE-002",
                re.compile(
                    r"^\s*(?:System|Assistant|Human|User)\s*:\s*(?:You are now|Forget|Ignore|From now on)",
                    re.IGNORECASE | re.MULTILINE
                ),
                Severity.CRITICAL,
                "Simulated conversation role injection."
            ),
        ]

    def scan(self, context: GatewayContext) -> Tuple[List[ThreatFinding], float]:
        """Scans the gateway context for deterministic threats.
        
        Inspects normalized analysis copy while checking original content for
        obfuscation (such as zero-width Unicode characters).
        
        Returns:
            Tuple of (findings_list, elapsed_ms)
        """
        start_time = time.perf_counter()
        findings: List[ThreatFinding] = []
        seen_rules = set()

        # 1. Zero-width / Unicode obfuscation evasion detection
        if context.has_zero_width_chars:
            # Find the first match in original content
            match = ZERO_WIDTH_PATTERN.search(context.original_content)
            start_off = match.start() if match else 0
            end_off = match.end() if match else 0
            findings.append(
                ThreatFinding(
                    rule_id="RULE-OBF-001",
                    category=ThreatCategory.INSTRUCTION_OVERRIDE,
                    severity=Severity.HIGH,
                    start_offset=start_off,
                    end_offset=end_off,
                    redacted_preview="[ZERO_WIDTH_OBFUSCATION_REDACTED]",
                    description="Hidden zero-width Unicode characters detected (filter evasion attempt)."
                )
            )
            seen_rules.add("RULE-OBF-001")

        # Helper to run a rule suite against both normalized and original text
        def run_rules(rule_list, category: ThreatCategory):
            for rule_id, regex, severity, desc in rule_list:
                # Scan normalized text first
                for match in regex.finditer(context.normalized_content):
                    dedup_key = (rule_id, match.start(), match.end())
                    if dedup_key in seen_rules:
                        continue
                    seen_rules.add(dedup_key)
                    raw_matched = match.group(0)
                    redacted = redact_secret_string(raw_matched, category, rule_id)
                    findings.append(
                        ThreatFinding(
                            rule_id=rule_id,
                            category=category,
                            severity=severity,
                            start_offset=match.start(),
                            end_offset=match.end(),
                            redacted_preview=redacted,
                            description=desc
                        )
                    )

        run_rules(self.rules_instruction_override, ThreatCategory.INSTRUCTION_OVERRIDE)
        run_rules(self.rules_prompt_extraction, ThreatCategory.SYSTEM_PROMPT_EXTRACTION)
        run_rules(self.rules_credential_exfiltration, ThreatCategory.CREDENTIAL_EXFILTRATION)
        run_rules(self.rules_unauthorized_transmission, ThreatCategory.UNAUTHORIZED_TRANSMISSION)
        run_rules(self.rules_role_manipulation, ThreatCategory.ROLE_MANIPULATION)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return findings, round(elapsed_ms, 3)
