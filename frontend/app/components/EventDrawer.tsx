"use client";

import React, { useEffect } from "react";

export interface SecurityEvent {
  request_id: string;
  turn_id?: string | null;
  timestamp: string;
  source: string;
  decision: "SAFE" | "SANITIZE" | "REVIEW" | "BLOCK" | string;
  risk_score: number;
  threat_categories: string[];
  triggered_rule_ids: string[];
  matched_policy_ids: string[];
  latency: {
    scanner_ms?: number;
    moss_ms?: number | null;
    llm_ms?: number | null;
    total_ms?: number;
    voice_to_decision_ms?: number;
  };
  redacted_preview: string;
  sanitized_preview?: string | null;
  approved_context_available: boolean;
  participant_identity?: string | null;
  room_name?: string | null;
  llm?: {
    called: boolean;
    status: string;
    model?: string;
    reason_called?: string;
  } | null;
}

interface EventDrawerProps {
  event: SecurityEvent | null;
  onClose: () => void;
}

export function EventDrawer({ event, onClose }: EventDrawerProps) {
  // ESC key handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!event) return null;

  const isSafe = event.decision === "SAFE";
  const isSanitize = event.decision === "SANITIZE";
  const isReview = event.decision === "REVIEW";
  const isBlock = event.decision === "BLOCK";

  const badgeColor = isSafe
    ? "var(--badge-safe-text)"
    : isSanitize
    ? "var(--badge-san-text)"
    : isReview
    ? "var(--badge-rev-text)"
    : "var(--badge-blk-text)";

  const badgeBg = isSafe
    ? "var(--badge-safe-bg)"
    : isSanitize
    ? "var(--badge-san-bg)"
    : isReview
    ? "var(--badge-rev-bg)"
    : "var(--badge-blk-bg)";

  const badgeBorder = isSafe
    ? "var(--badge-safe-border)"
    : isSanitize
    ? "var(--badge-san-border)"
    : isReview
    ? "var(--badge-rev-border)"
    : "var(--badge-blk-border)";

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(2px)",
        zIndex: 50,
        display: "flex",
        justifyContent: "flex-end",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "540px",
          height: "100%",
          backgroundColor: "var(--bg-card)",
          borderLeft: "1px solid var(--border-strong)",
          display: "flex",
          flexDirection: "column",
          boxShadow: "-4px 0 24px rgba(0, 0, 0, 0.5)",
          overflowY: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Security Event Detail"
      >
        {/* Drawer Header */}
        <div
          style={{
            padding: "1.25rem 1.5rem",
            borderBottom: "1px solid var(--border-subtle)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <span
              style={{
                fontSize: "0.875rem",
                fontWeight: 700,
                padding: "0.25rem 0.625rem",
                borderRadius: "4px",
                backgroundColor: badgeBg,
                color: badgeColor,
                border: `1px solid ${badgeBorder}`,
                letterSpacing: "0.05em",
              }}
            >
              {event.decision}
            </span>
            <div>
              <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                Security Event Inspection
              </h2>
              <span className="font-mono" style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                ID: {event.request_id || "N/A"}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-secondary)",
              fontSize: "1.25rem",
              cursor: "pointer",
              padding: "0.25rem",
              borderRadius: "4px",
            }}
            aria-label="Close detail drawer"
          >
            ✕
          </button>
        </div>

        {/* Drawer Content */}
        <div style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div>
            <h3 style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--text-primary)" }}>Decision Summary</h3>
            <p style={{ marginTop: "0.2rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              The gateway verdict and the context-delivery boundary for this event.
            </p>
          </div>
          {/* Key Attributes Grid */}
          <div
            className="drawer-section"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: "0.75rem",
              backgroundColor: "var(--bg-canvas)",
              padding: "1rem",
              borderRadius: "6px",
              border: "1px solid var(--border-subtle)",
              fontSize: "0.8125rem",
            }}
          >
            <div>
              <span style={{ color: "var(--text-muted)", fontSize: "0.6875rem" }}>INGESTION SOURCE</span>
              <div style={{ fontWeight: 600, color: "var(--text-primary)", marginTop: "0.125rem" }}>
                {event.source === "livekit_voice" ? "🎙️ LiveKit Real-Time Voice" : `🌐 ${event.source}`}
              </div>
            </div>

            <div>
              <span style={{ color: "var(--text-muted)", fontSize: "0.6875rem" }}>RISK SCORE</span>
              <div style={{ fontWeight: 700, color: badgeColor, marginTop: "0.125rem" }}>
                {event.risk_score} / 100
              </div>
            </div>

            <div>
              <span style={{ color: "var(--text-muted)", fontSize: "0.6875rem" }}>TIMESTAMP</span>
              <div style={{ color: "var(--text-secondary)", marginTop: "0.125rem" }}>
                {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : "N/A"}
              </div>
            </div>

            <div>
              <span style={{ color: "var(--text-muted)", fontSize: "0.6875rem" }}>PARTICIPANT / SENDER</span>
              <div style={{ color: "var(--text-secondary)", marginTop: "0.125rem" }}>
                {event.participant_identity || "anonymous_user"}
              </div>
            </div>
          </div>

          {/* CRITICAL: Protected Agent Security Boundary Panel */}
          <div
            className="drawer-section"
            style={{
              borderRadius: "8px",
              padding: "1rem 1.25rem",
              backgroundColor: isSafe
                ? "rgba(16, 185, 129, 0.06)"
                : isSanitize
                ? "rgba(6, 182, 212, 0.06)"
                : "rgba(239, 68, 68, 0.06)",
              border: `1px solid ${
                isSafe
                  ? "rgba(16, 185, 129, 0.25)"
                  : isSanitize
                  ? "rgba(6, 182, 212, 0.25)"
                  : "rgba(239, 68, 68, 0.25)"
              }`,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "1rem" }}>🛡️</span>
              <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Protected Agent Boundary
              </h3>
            </div>

            <div style={{ marginTop: "0.75rem", fontSize: "0.8125rem" }}>
              {isBlock ? (
                <div style={{ color: "#ef4444", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                  <strong>ATTACK CONTAINED — NO CONTEXT DELIVERED</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Hostile payload was intercepted by ContextShield. Downstream AI agent received null context.
                  </span>
                </div>
              ) : isReview ? (
                <div style={{ color: "#f59e0b", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                  <strong>AMBIGUOUS INTENT — CONTEXT WITHHELD</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Potentially unauthorized sensitive action detected. Context blocked pending SOC authorization.
                  </span>
                </div>
              ) : isSanitize ? (
                <div style={{ color: "#06b6d4", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                  <strong>SANITIZED CONTEXT DELIVERED</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Hostile prompt injection was excised. Only clean, verified content reached the agent.
                  </span>
                  {event.sanitized_preview && (
                    <div
                      className="font-mono"
                      style={{
                        marginTop: "0.5rem",
                        padding: "0.5rem",
                        borderRadius: "4px",
                        backgroundColor: "var(--bg-card)",
                        border: "1px solid var(--border-subtle)",
                        fontSize: "0.75rem",
                        color: "var(--text-primary)",
                      }}
                    >
                      {event.sanitized_preview}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ color: "#10b981", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                  <strong>BENIGN CONTEXT DELIVERED</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Zero threat indicators detected. Approved context delivered intact to recipient agent.
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Timing Breakdown Bar */}
          <div>
            <h3 style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
              Pipeline latency
            </h3>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: "0.5rem",
                marginTop: "0.5rem",
                textAlign: "center",
              }}
            >
              <div style={{ padding: "0.5rem", backgroundColor: "var(--bg-canvas)", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", display: "block" }}>SCANNER</span>
                <strong className="font-mono" style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
                  {event.latency.scanner_ms !== undefined ? `${event.latency.scanner_ms} ms` : "—"}
                </strong>
              </div>

              <div style={{ padding: "0.5rem", backgroundColor: "var(--bg-canvas)", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", display: "block" }}>MOSS</span>
                <strong className="font-mono" style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
                  {event.latency.moss_ms !== null && event.latency.moss_ms !== undefined
                    ? `${event.latency.moss_ms} ms`
                    : "—"}
                </strong>
              </div>

              <div style={{ padding: "0.5rem", backgroundColor: "var(--bg-canvas)", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", display: "block" }}>GEMINI</span>
                <strong className="font-mono" style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
                  {event.llm?.called ? `${event.latency.llm_ms || "—"} ms` : "Skipped"}
                </strong>
              </div>

              <div style={{ padding: "0.5rem", backgroundColor: "var(--bg-canvas)", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", display: "block" }}>TOTAL</span>
                <strong className="font-mono" style={{ fontSize: "0.8125rem", color: "var(--accent-blue)" }}>
                  {event.latency.total_ms !== undefined ? `${event.latency.total_ms} ms` : "—"}
                </strong>
              </div>
            </div>

            {event.latency.voice_to_decision_ms !== undefined && (
              <div
                style={{
                  marginTop: "0.5rem",
                  padding: "0.375rem 0.75rem",
                  borderRadius: "4px",
                  backgroundColor: "rgba(16, 185, 129, 0.08)",
                  border: "1px solid rgba(16, 185, 129, 0.2)",
                  fontSize: "0.75rem",
                  color: "#10b981",
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <span>LiveKit Voice-to-Decision Total:</span>
                <strong className="font-mono">{event.latency.voice_to_decision_ms} ms</strong>
              </div>
            )}
          </div>

          {/* MANDATORY DISTINCTION: Retrieved Moss Policies vs Applied Security Evidence */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {/* Applied Security Evidence */}
            <div className="drawer-section drawer-section--evidence">
              <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
                <span style={{ fontSize: "0.8125rem" }}>⚖️</span>
                <h3 style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  Applied Security Evidence (Decision Drivers)
                </h3>
              </div>
              <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.125rem" }}>
                Deterministic scanner findings and verified evidence that enforced the final verdict:
              </p>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.375rem", marginTop: "0.5rem" }}>
                {event.triggered_rule_ids && event.triggered_rule_ids.length > 0 ? (
                  event.triggered_rule_ids.map((rule) => (
                    <span
                      key={rule}
                      className="font-mono"
                      style={{
                        fontSize: "0.6875rem",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "4px",
                        backgroundColor: "rgba(239, 68, 68, 0.12)",
                        color: "#ef4444",
                        border: "1px solid rgba(239, 68, 68, 0.3)",
                      }}
                    >
                      {rule}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                    No deterministic threat rules triggered (Clean payload).
                  </span>
                )}
              </div>
            </div>

            {/* Retrieved Moss Policies */}
            <div className="drawer-section drawer-section--retrieval">
              <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
                <span style={{ fontSize: "0.8125rem" }}>🔍</span>
                <h3 style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  Retrieved Moss Policies (Semantic Candidates)
                </h3>
              </div>
              <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.125rem" }}>
                Relevant policy documents retrieved by Moss Local Runtime for semantic alignment:
              </p>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.375rem", marginTop: "0.5rem" }}>
                {event.matched_policy_ids && event.matched_policy_ids.length > 0 ? (
                  event.matched_policy_ids.map((pid) => (
                    <span
                      key={pid}
                      className="font-mono"
                      style={{
                        fontSize: "0.6875rem",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "4px",
                        backgroundColor: "rgba(59, 130, 246, 0.1)",
                        color: "var(--accent-blue)",
                        border: "1px solid rgba(59, 130, 246, 0.3)",
                      }}
                    >
                      {pid}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                    No high-similarity Moss policies retrieved for this pattern.
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Privacy-Safe Redacted Preview */}
          <div>
            <h3 style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
              Privacy-Preserving Audit Preview
            </h3>
            <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.125rem" }}>
              Raw hostile context, API keys, and sensitive tokens are permanently scrubbed:
            </p>
            <div
              className="font-mono"
              style={{
                marginTop: "0.5rem",
                padding: "0.75rem",
                borderRadius: "4px",
                backgroundColor: "var(--bg-canvas)",
                border: "1px solid var(--border-subtle)",
                fontSize: "0.75rem",
                color: "var(--text-secondary)",
                wordBreak: "break-word",
                maxHeight: "120px",
                overflowY: "auto",
              }}
            >
              {event.redacted_preview || "No preview recorded"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
