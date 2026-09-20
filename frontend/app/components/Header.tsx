"use client";

import React from "react";

export interface HealthData {
  gateway: string;
  moss: { status: string; loaded: boolean; index_name?: string };
  gemini: { configured: boolean; model?: string; last_status?: string };
  livekit: { last_voice_event_at?: string | null; recent_activity: boolean };
}

interface HeaderProps {
  health: HealthData | null;
  theme: "dark" | "light";
  onToggleTheme: () => void;
  onOpenSimulate: () => void;
  refreshing: boolean;
  onRefresh: () => void;
  backendAvailable?: boolean;
}

export function Header({
  health,
  theme,
  onToggleTheme,
  onOpenSimulate,
  refreshing,
  onRefresh,
  backendAvailable = true,
}: HeaderProps) {
  const isHealthy = backendAvailable && health?.gateway === "healthy";
  const mossReady = health?.moss?.status === "ready" && health.moss.loaded === true;
  const mossStatus = health?.moss?.status || "unknown";
  const geminiStatus = health?.gemini?.last_status || "not_called";
  const hasRecentVoice = health?.livekit?.recent_activity;

  return (
    <header
      className="app-header"
      style={{
        borderBottom: "1px solid var(--border-subtle)",
        backgroundColor: "var(--bg-card)",
        padding: "0.875rem 1.5rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "1rem",
        position: "sticky",
        top: 0,
        zIndex: 30,
      }}
    >
      {/* Brand & System Status */}
      <div className="header-brand" style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "6px",
              backgroundColor: "var(--accent-blue)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              fontWeight: 700,
              fontSize: "0.875rem",
              boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
            }}
          >
            CS
          </div>
          <div>
            <h1
              style={{
                fontSize: "1.125rem",
                fontWeight: 700,
                letterSpacing: "-0.025em",
                color: "var(--text-primary)",
                lineHeight: 1.2,
              }}
            >
              ContextShield
            </h1>
            <span
              style={{
                fontSize: "0.6875rem",
                color: "var(--text-muted)",
                letterSpacing: "0.02em",
                textTransform: "uppercase",
              }}
            >
              Low-Latency AI Context Security Gateway
            </span>
          </div>
        </div>

        {/* Status Pulse */}
        <div
          className="gateway-chip"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.25rem 0.625rem",
            borderRadius: "9999px",
            backgroundColor: isHealthy ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
            border: `1px solid ${isHealthy ? "rgba(16, 185, 129, 0.25)" : "rgba(239, 68, 68, 0.25)"}`,
            fontSize: "0.75rem",
            fontWeight: 500,
            color: isHealthy ? "#10b981" : "#ef4444",
          }}
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              backgroundColor: isHealthy ? "#10b981" : "#ef4444",
              display: "inline-block",
            }}
            className="animate-pulse-slow"
          />
          {isHealthy ? "Gateway Operational" : !backendAvailable ? "Backend Unavailable" : "Gateway Connecting..."}
        </div>
      </div>

      {/* Subsystem Verifiable Health Badges */}
      <div
        className="status-cluster"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        {/* Moss Local Runtime */}
        <div
          className="status-chip"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
            fontSize: "0.75rem",
            padding: "0.25rem 0.5rem",
            borderRadius: "4px",
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
          }}
          title={`Moss Index: ${health?.moss?.index_name || "contextshield-security"}`}
        >
          <span className="status-chip-dot" style={{ backgroundColor: mossReady ? "#10b981" : mossStatus === "error" ? "#f59e0b" : "var(--text-muted)" }} />
          <span style={{ color: "var(--text-muted)", fontSize: "0.6875rem" }}>Moss</span>
          <span
            style={{
              fontWeight: 600,
              color: mossReady ? "#10b981" : mossStatus === "error" ? "#f59e0b" : "var(--text-muted)",
            }}
          >
            {mossReady
              ? "Ready"
              : mossStatus === "error"
              ? "Fail-Secure"
              : mossStatus === "not_configured"
              ? "Not Configured"
              : mossStatus}
          </span>
        </div>

        {/* Gemini Evaluator */}
        <div
          className="status-chip"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
            fontSize: "0.75rem",
            padding: "0.25rem 0.5rem",
            borderRadius: "4px",
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
          }}
          title={health?.gemini?.model ? `Model: ${health.gemini.model}` : "Gemini Evaluator"}
        >
          <span className="status-chip-dot" style={{ backgroundColor: geminiStatus === "success" ? "#10b981" : geminiStatus === "rate_limited" ? "#f59e0b" : "var(--text-muted)" }} />
          <span style={{ color: "var(--text-muted)", fontSize: "0.6875rem" }}>Gemini</span>
          <span
            style={{
              fontWeight: 600,
              color:
                geminiStatus === "success"
                  ? "#10b981"
                  : geminiStatus === "rate_limited"
                  ? "#f59e0b"
                  : "var(--text-secondary)",
            }}
          >
            {geminiStatus === "not_called" ? "Standby" : geminiStatus}
          </span>
        </div>

        {/* LiveKit Voice Cloud */}
        <div
          className="status-chip"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
            fontSize: "0.75rem",
            padding: "0.25rem 0.5rem",
            borderRadius: "4px",
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
          }}
          title="LiveKit Inference STT (deepgram/nova-3)"
        >
          <span className="status-chip-dot" style={{ backgroundColor: hasRecentVoice ? "#10b981" : "var(--text-muted)" }} />
          <span style={{ color: "var(--text-muted)", fontSize: "0.6875rem" }}>Voice</span>
          <span
            style={{
              fontWeight: 600,
              color: hasRecentVoice ? "#10b981" : "var(--text-secondary)",
            }}
          >
            {hasRecentVoice ? "Active" : "Online"}
          </span>
        </div>

        {/* Manual Refresh Indicator */}
        <div className="header-actions">
        <button
          onClick={onRefresh}
          disabled={refreshing}
          style={{
            padding: "0.375rem 0.625rem",
            borderRadius: "4px",
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
            fontSize: "0.75rem",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
          }}
          title="Polling every 1.5s (Click to force refresh)"
        >
          <span style={{ transform: refreshing ? "rotate(180deg)" : "none", transition: "transform 0.3s" }}>
            ↻
          </span>
          {refreshing ? "Refreshing..." : "1.5s"}
        </button>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          style={{
            padding: "0.375rem 0.625rem",
            borderRadius: "4px",
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
            fontSize: "0.8125rem",
            cursor: "pointer",
          }}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
        </button>

        {/* Simulate Threat Action */}
        <button
          onClick={onOpenSimulate}
          style={{
            padding: "0.4rem 0.875rem",
            borderRadius: "6px",
            backgroundColor: "var(--accent-blue)",
            border: "none",
            color: "#ffffff",
            fontSize: "0.8125rem",
            fontWeight: 600,
            cursor: "pointer",
            boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
          }}
        >
          ⚡ Simulate Ingestion
        </button>
        </div>
      </div>
    </header>
  );
}
