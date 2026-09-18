"use client";

import React, { useState } from "react";
import { SecurityEvent } from "./EventDrawer";

interface LiveFeedProps {
  events: SecurityEvent[];
  onSelectEvent: (event: SecurityEvent) => void;
  loading: boolean;
}

export function LiveFeed({ events, onSelectEvent, loading }: LiveFeedProps) {
  const [filterSource, setFilterSource] = useState<string>("all");
  const [filterDecision, setFilterDecision] = useState<string>("all");

  const filteredEvents = events.filter((e) => {
    if (filterSource === "voice" && e.source !== "livekit_voice") return false;
    if (filterSource === "non-voice" && e.source === "livekit_voice") return false;
    if (filterDecision !== "all" && e.decision !== filterDecision) return false;
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Filter Toolbar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "0.75rem",
          padding: "0.75rem 1rem",
          backgroundColor: "var(--bg-card)",
          borderRadius: "6px",
          border: "1px solid var(--border-subtle)",
        }}
      >
        {/* Source Filter */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginRight: "0.25rem" }}>
            Source:
          </span>
          {[
            { key: "all", label: "All Sources" },
            { key: "voice", label: "🎙️ LiveKit Voice Only" },
            { key: "non-voice", label: "🌐 API & Web" },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilterSource(f.key)}
              style={{
                padding: "0.25rem 0.625rem",
                borderRadius: "4px",
                fontSize: "0.75rem",
                fontWeight: filterSource === f.key ? 600 : 400,
                backgroundColor: filterSource === f.key ? "var(--bg-canvas)" : "transparent",
                color: filterSource === f.key ? "var(--text-primary)" : "var(--text-secondary)",
                border: filterSource === f.key ? "1px solid var(--border-strong)" : "1px solid transparent",
                cursor: "pointer",
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Decision Filter */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginRight: "0.25rem" }}>
            Decision:
          </span>
          {[
            { key: "all", label: "All" },
            { key: "SAFE", label: "SAFE", color: "#10b981" },
            { key: "SANITIZE", label: "SANITIZE", color: "#06b6d4" },
            { key: "REVIEW", label: "REVIEW", color: "#f59e0b" },
            { key: "BLOCK", label: "BLOCK", color: "#ef4444" },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilterDecision(f.key)}
              style={{
                padding: "0.25rem 0.5rem",
                borderRadius: "4px",
                fontSize: "0.6875rem",
                fontWeight: 600,
                backgroundColor: filterDecision === f.key ? "var(--bg-canvas)" : "transparent",
                color: f.color || (filterDecision === f.key ? "var(--text-primary)" : "var(--text-secondary)"),
                border: filterDecision === f.key ? "1px solid var(--border-strong)" : "1px solid transparent",
                cursor: "pointer",
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Events List */}
      {loading && events.length === 0 ? (
        <div
          style={{
            padding: "3rem",
            textAlign: "center",
            color: "var(--text-muted)",
            fontSize: "0.875rem",
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            border: "1px solid var(--border-subtle)",
          }}
        >
          Loading session events from ContextShield Gateway...
        </div>
      ) : filteredEvents.length === 0 ? (
        <div
          style={{
            padding: "3rem",
            textAlign: "center",
            color: "var(--text-muted)",
            fontSize: "0.875rem",
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            border: "1px solid var(--border-subtle)",
          }}
        >
          No events found matching selected filters.
          <p style={{ fontSize: "0.75rem", marginTop: "0.5rem" }}>
            Trigger an evaluation using the <strong>"Simulate Ingestion"</strong> button above or speak into the LiveKit Console microphone.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
          {filteredEvents.map((ev, index) => {
            const isSafe = ev.decision === "SAFE";
            const isSanitize = ev.decision === "SANITIZE";
            const isReview = ev.decision === "REVIEW";
            const isBlock = ev.decision === "BLOCK";

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
                key={ev.request_id || index}
                onClick={() => onSelectEvent(ev)}
                style={{
                  backgroundColor: "var(--bg-card)",
                  borderRadius: "8px",
                  padding: "0.875rem 1.125rem",
                  border: "1px solid var(--border-subtle)",
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                  transition: "border-color 0.15s ease, background-color 0.15s ease",
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
                {/* Top Row: Badges, Source, Timing, Timestamp */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "0.5rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        padding: "0.15rem 0.5rem",
                        borderRadius: "4px",
                        backgroundColor: badgeBg,
                        color: badgeColor,
                        border: `1px solid ${badgeBorder}`,
                        letterSpacing: "0.02em",
                      }}
                    >
                      {ev.decision}
                    </span>

                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        color: "var(--text-primary)",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.25rem",
                      }}
                    >
                      {ev.source === "livekit_voice" ? "🎙️ LiveKit Voice" : `🌐 ${ev.source}`}
                    </span>

                    {ev.turn_id && (
                      <span
                        className="font-mono"
                        style={{
                          fontSize: "0.6875rem",
                          color: "var(--text-muted)",
                          padding: "0.1rem 0.35rem",
                          borderRadius: "3px",
                          backgroundColor: "var(--bg-canvas)",
                        }}
                      >
                        turn:{ev.turn_id.slice(0, 8)}
                      </span>
                    )}
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.75rem" }}>
                    <span style={{ color: "var(--text-muted)" }}>
                      Risk: <strong style={{ color: badgeColor }}>{ev.risk_score}/100</strong>
                    </span>

                    <span className="font-mono" style={{ color: "var(--accent-blue)" }}>
                      {ev.latency.total_ms ? `${ev.latency.total_ms}ms` : "—"}
                    </span>

                    <span style={{ color: "var(--text-muted)" }}>
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : "—"}
                    </span>
                  </div>
                </div>

                {/* Middle: Redacted preview snippet */}
                <div
                  className="font-mono"
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--text-secondary)",
                    backgroundColor: "var(--bg-canvas)",
                    padding: "0.375rem 0.625rem",
                    borderRadius: "4px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {ev.redacted_preview || "No preview recorded"}
                </div>

                {/* Bottom Row: Metadata tags & Protected Agent Indicator */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "0.5rem",
                    fontSize: "0.6875rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.375rem", flexWrap: "wrap" }}>
                    {ev.threat_categories.map((cat) => (
                      <span
                        key={cat}
                        style={{
                          padding: "0.1rem 0.35rem",
                          borderRadius: "3px",
                          backgroundColor: "var(--bg-card-secondary)",
                          color: "var(--text-secondary)",
                          border: "1px solid var(--border-subtle)",
                        }}
                      >
                        {cat}
                      </span>
                    ))}

                    {ev.matched_policy_ids && ev.matched_policy_ids.length > 0 && (
                      <span style={{ color: "var(--text-muted)" }}>
                        Policies: {ev.matched_policy_ids.slice(0, 3).join(", ")}
                        {ev.matched_policy_ids.length > 3 ? "..." : ""}
                      </span>
                    )}

                    {ev.llm?.called && (
                      <span
                        style={{
                          padding: "0.1rem 0.35rem",
                          borderRadius: "3px",
                          backgroundColor: "rgba(139, 92, 246, 0.1)",
                          color: "var(--accent-purple)",
                          border: "1px solid rgba(139, 92, 246, 0.3)",
                        }}
                      >
                        Gemini: {ev.llm.status}
                      </span>
                    )}
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span
                      style={{
                        fontWeight: 500,
                        color: isSafe || isSanitize ? "#10b981" : "#ef4444",
                      }}
                    >
                      {isSafe || isSanitize ? "✓ Context Delivered" : "✗ Context Blocked"}
                    </span>
                    <span style={{ color: "var(--text-muted)" }}>View Details →</span>
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
