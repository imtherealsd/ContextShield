"use client";

import React from "react";

export interface DashboardStats {
  session_label: string;
  is_session_data: boolean;
  total_evaluated: number;
  safe_count: number;
  sanitize_count: number;
  review_count: number;
  block_count: number;
  safe_pct: number;
  sanitize_pct: number;
  review_pct: number;
  block_pct: number;
  average_risk_score: number | null;
  average_scanner_ms: number | null;
  average_moss_ms: number | null;
  average_total_ms: number | null;
  average_voice_to_decision_ms: number | null;
  gemini_called_count: number;
  gemini_skipped_count: number;
  gemini_invocation_rate: number;
  gemini_skip_rate: number;
  voice_turns_count: number;
}

interface MetricsOverviewProps {
  stats: DashboardStats | null;
}

export function MetricsOverview({ stats }: MetricsOverviewProps) {
  const total = stats?.total_evaluated ?? 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Session Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "0.625rem 1rem",
          borderRadius: "6px",
          backgroundColor: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          fontSize: "0.75rem",
          color: "var(--text-secondary)",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ color: "var(--accent-blue)", fontWeight: 600 }}>● Telemetry Scope:</span>
          <span>{stats?.session_label || "Current Session"}</span>
          {stats?.is_session_data !== false && (
            <span style={{ color: "var(--text-muted)" }}>• Counters reset on server restart</span>
          )}
        </div>
        <div style={{ color: "var(--text-muted)" }}>
          Total Evaluated Turns: <strong style={{ color: "var(--text-primary)" }}>{total}</strong>
        </div>
      </div>

      {/* Decision Summary KPI Grid */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "1rem", flexWrap: "wrap" }}>
        <div>
          <h2 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)" }}>Decision outcomes</h2>
          <p style={{ marginTop: "0.2rem", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            Every evaluated turn ends at an explicit protected-agent boundary.
          </p>
        </div>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Delivery status by decision</span>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
        }}
      >
        {/* SAFE */}
        <div
          className="decision-card"
          style={{
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            padding: "1.125rem",
            border: "1px solid var(--border-subtle)",
            borderLeft: "4px solid #10b981",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500 }}>
              SAFE
            </span>
            <span
              style={{
                fontSize: "0.6875rem",
                padding: "0.125rem 0.375rem",
                borderRadius: "4px",
                backgroundColor: "var(--badge-safe-bg)",
                color: "var(--badge-safe-text)",
                fontWeight: 600,
              }}
            >
              {stats?.safe_pct ?? 0}%
            </span>
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.375rem" }}>
            {stats?.safe_count ?? 0}
          </div>
          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
            Original context delivered
          </span>
        </div>

        {/* SANITIZE */}
        <div
          className="decision-card"
          style={{
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            padding: "1.125rem",
            border: "1px solid var(--border-subtle)",
            borderLeft: "4px solid #06b6d4",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500 }}>
              SANITIZE
            </span>
            <span
              style={{
                fontSize: "0.6875rem",
                padding: "0.125rem 0.375rem",
                borderRadius: "4px",
                backgroundColor: "var(--badge-san-bg)",
                color: "var(--badge-san-text)",
                fontWeight: 600,
              }}
            >
              {stats?.sanitize_pct ?? 0}%
            </span>
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.375rem" }}>
            {stats?.sanitize_count ?? 0}
          </div>
          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
            Unsafe fragments removed
          </span>
        </div>

        {/* REVIEW */}
        <div
          className="decision-card"
          style={{
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            padding: "1.125rem",
            border: "1px solid var(--border-subtle)",
            borderLeft: "4px solid #f59e0b",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500 }}>
              REVIEW
            </span>
            <span
              style={{
                fontSize: "0.6875rem",
                padding: "0.125rem 0.375rem",
                borderRadius: "4px",
                backgroundColor: "var(--badge-rev-bg)",
                color: "var(--badge-rev-text)",
                fontWeight: 600,
              }}
            >
              {stats?.review_pct ?? 0}%
            </span>
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.375rem" }}>
            {stats?.review_count ?? 0}
          </div>
          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
            Context withheld for review
          </span>
        </div>

        {/* BLOCK */}
        <div
          className="decision-card"
          style={{
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            padding: "1.125rem",
            border: "1px solid var(--border-subtle)",
            borderLeft: "4px solid #ef4444",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500 }}>
              BLOCK
            </span>
            <span
              style={{
                fontSize: "0.6875rem",
                padding: "0.125rem 0.375rem",
                borderRadius: "4px",
                backgroundColor: "var(--badge-blk-bg)",
                color: "var(--badge-blk-text)",
                fontWeight: 600,
              }}
            >
              {stats?.block_pct ?? 0}%
            </span>
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.375rem" }}>
            {stats?.block_count ?? 0}
          </div>
          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
            No context reached agent
          </span>
        </div>
      </div>

      {/* Observed Latency Metrics & LLM Gating */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        {/* Pipeline Performance */}
        <div
          style={{
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            padding: "1.25rem",
            border: "1px solid var(--border-subtle)",
            display: "flex",
            flexDirection: "column",
            gap: "0.875rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
              ⚡ Pipeline Performance
            </h3>
            <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Real Session Averages</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
            {/* Scanner */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8125rem" }}>
              <span style={{ color: "var(--text-secondary)" }}>Deterministic Scanner:</span>
              <strong className="font-mono" style={{ color: "var(--text-primary)" }}>
                {stats?.average_scanner_ms !== null && stats?.average_scanner_ms !== undefined
                  ? `${stats.average_scanner_ms} ms`
                  : "—"}
              </strong>
            </div>

            {/* Moss */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8125rem" }}>
              <span style={{ color: "var(--text-secondary)" }}>Moss Semantic Retrieval:</span>
              <strong className="font-mono" style={{ color: "var(--text-primary)" }}>
                {stats?.average_moss_ms !== null && stats?.average_moss_ms !== undefined
                  ? `${stats.average_moss_ms} ms`
                  : "No observed query"}
              </strong>
            </div>

            {/* Total Gateway */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8125rem" }}>
              <span style={{ color: "var(--text-secondary)" }}>Total Gateway Pipeline:</span>
              <strong className="font-mono" style={{ color: "var(--accent-blue)" }}>
                {stats?.average_total_ms !== null && stats?.average_total_ms !== undefined
                  ? `${stats.average_total_ms} ms`
                  : "—"}
              </strong>
            </div>

            {/* LiveKit Voice-to-Decision */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8125rem" }}>
              <span style={{ color: "var(--text-secondary)" }}>Voice-to-Decision (LiveKit):</span>
              <strong className="font-mono" style={{ color: "#10b981" }}>
                {stats?.average_voice_to_decision_ms !== null && stats?.average_voice_to_decision_ms !== undefined
                  ? `${stats.average_voice_to_decision_ms} ms`
                  : "Recorded on turn"}
              </strong>
            </div>
          </div>
        </div>

        {/* Gemini Gating & Skip Ratio */}
        <div
          style={{
            backgroundColor: "var(--bg-card)",
            borderRadius: "8px",
            padding: "1.25rem",
            border: "1px solid var(--border-subtle)",
            display: "flex",
            flexDirection: "column",
            gap: "0.875rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
              🎯 LLM Gating Efficiency
            </h3>
            <span
              style={{
                fontSize: "0.6875rem",
                padding: "0.125rem 0.375rem",
                borderRadius: "4px",
                backgroundColor: "rgba(59, 130, 246, 0.1)",
                color: "var(--accent-blue)",
                fontWeight: 600,
              }}
            >
              Ambiguity only
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
            <span style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)" }}>
              {stats?.gemini_skip_rate ?? 100}%
            </span>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              LLM evaluations avoided
            </span>
          </div>

          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
            Clear decisions use the fast deterministic path; Gemini is reserved for ambiguous cases.
          </p>

          <div className="llm-stat-grid">
            <div className="llm-stat">
              Skipped: <strong style={{ color: "#10b981" }}>{stats?.gemini_skipped_count ?? 0}</strong>
            </div>
            <div className="llm-stat">
              Called: <strong style={{ color: "var(--text-primary)" }}>{stats?.gemini_called_count ?? 0}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
