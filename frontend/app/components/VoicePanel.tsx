"use client";

import React from "react";
import { SecurityEvent } from "./EventDrawer";

interface VoicePanelProps {
  voiceTurns: any[];
  onSelectEvent: (event: SecurityEvent) => void;
}

export function VoicePanel({ voiceTurns, onSelectEvent }: VoicePanelProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Voice Architecture Banner */}
      <div
        style={{
          padding: "1rem 1.25rem",
          borderRadius: "8px",
          backgroundColor: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "1.25rem" }}>🎙️</span>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)" }}>
              LiveKit Real-Time Voice Ingestion
            </h2>
            <span
              style={{
                fontSize: "0.6875rem",
                padding: "0.125rem 0.5rem",
                borderRadius: "9999px",
                backgroundColor: "rgba(16, 185, 129, 0.1)",
                color: "#10b981",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                fontWeight: 600,
              }}
            >
              deepgram/nova-3 STT
            </span>
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            Real-time audio transcribed on LiveKit Cloud (`India South`) and gated through ContextShield before any text reaches recipient AI agents.
          </p>
        </div>

        {/* Privacy Invariant Seal */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.5rem 0.75rem",
            borderRadius: "6px",
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-strong)",
            fontSize: "0.75rem",
            color: "var(--text-secondary)",
          }}
        >
          <span style={{ color: "#10b981", fontSize: "0.875rem" }}>🔒</span>
          <span>Zero raw hostile audio or transcripts stored in telemetry</span>
        </div>
      </div>

      {/* Voice Turns List */}
      {voiceTurns.length === 0 ? (
        <div
          style={{
            padding: "3.5rem",
            textAlign: "center",
            color: "var(--text-muted)",
            fontSize: "0.875rem",
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            border: "1px solid var(--border-subtle)",
          }}
        >
          No LiveKit voice turns recorded in current session.
          <p style={{ fontSize: "0.75rem", marginTop: "0.5rem" }}>
            Speak into your microphone in the open LiveKit Console window to stream live audio turns through the pipeline.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {voiceTurns.map((turn, idx) => {
            const isSafe = turn.decision === "SAFE";
            const isBlock = turn.decision === "BLOCK";
            const isReview = turn.decision === "REVIEW";

            const badgeColor = isSafe ? "#10b981" : isReview ? "#f59e0b" : "#ef4444";
            const badgeBg = isSafe
              ? "rgba(16, 185, 129, 0.12)"
              : isReview
              ? "rgba(245, 158, 11, 0.12)"
              : "rgba(239, 68, 68, 0.12)";

            return (
              <div
                key={turn.turn_id || idx}
                onClick={() =>
                  onSelectEvent({
                    request_id: turn.request_id || turn.turn_id,
                    turn_id: turn.turn_id,
                    timestamp: turn.timestamp,
                    source: "livekit_voice",
                    decision: turn.decision,
                    risk_score: turn.risk_score,
                    threat_categories: turn.threat_categories || [],
                    triggered_rule_ids: turn.matched_policy_ids || [],
                    matched_policy_ids: turn.matched_policy_ids || [],
                    latency: {
                      moss_ms: turn.moss_ms,
                      total_ms: turn.shield_total_ms,
                      voice_to_decision_ms: turn.voice_to_decision_ms,
                    },
                    redacted_preview: turn.redacted_preview,
                    approved_context_available: turn.approved_context_available,
                    participant_identity: turn.participant_identity,
                    room_name: turn.room_name,
                    llm: turn.llm_called ? { called: true, status: turn.llm_status } : null,
                  })
                }
                style={{
                  backgroundColor: "var(--bg-card)",
                  borderRadius: "8px",
                  padding: "1rem 1.25rem",
                  border: "1px solid var(--border-subtle)",
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.625rem",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "var(--bg-card-hover)";
                  e.currentTarget.style.borderColor = "var(--border-strong)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "var(--bg-card)";
                  e.currentTarget.style.borderColor = "var(--border-subtle)";
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        padding: "0.15rem 0.5rem",
                        borderRadius: "4px",
                        backgroundColor: badgeBg,
                        color: badgeColor,
                        border: `1px solid ${badgeColor}40`,
                      }}
                    >
                      {turn.decision}
                    </span>

                    <span className="font-mono" style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      Turn ID: {turn.turn_id?.slice(0, 8) || "N/A"}
                    </span>

                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      Speaker: <strong style={{ color: "var(--text-secondary)" }}>{turn.participant_identity || "user"}</strong>
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.75rem" }}>
                    <span style={{ color: "var(--text-muted)" }}>
                      Risk: <strong style={{ color: badgeColor }}>{turn.risk_score}/100</strong>
                    </span>

                    <span className="font-mono" style={{ color: "#10b981", fontWeight: 600 }}>
                      Voice-to-Decision: {turn.voice_to_decision_ms ? `${turn.voice_to_decision_ms}ms` : "—"}
                    </span>
                  </div>
                </div>

                {/* Redacted Preview */}
                <div
                  className="font-mono"
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--text-secondary)",
                    backgroundColor: "var(--bg-canvas)",
                    padding: "0.375rem 0.625rem",
                    borderRadius: "4px",
                  }}
                >
                  {turn.redacted_preview || "No preview recorded"}
                </div>

                {/* Footer details */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                  <div>
                    Room: <code>{turn.room_name || "console-room"}</code> • Gateway: {turn.shield_total_ms || "—"}ms
                  </div>
                  <div style={{ color: isSafe ? "#10b981" : "#ef4444", fontWeight: 600 }}>
                    {turn.approved_context_available ? "✓ Approved Context Available" : "✗ Approved Context = Null"}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
