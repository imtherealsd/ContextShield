"use client";

import React, { useState } from "react";

export interface PolicyItem {
  id: string;
  category: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
  recommended_action: string;
  policy_version: string;
  text: string;
}

interface PoliciesViewProps {
  policies: PolicyItem[];
  mossIndexName?: string;
  mossStatus?: string;
}

export function PoliciesView({ policies, mossIndexName, mossStatus }: PoliciesViewProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");

  const filtered = policies.filter((p) => {
    if (severityFilter !== "all" && p.severity !== severityFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchId = p.id.toLowerCase().includes(q);
      const matchCat = p.category.toLowerCase().includes(q);
      const matchText = p.text.toLowerCase().includes(q);
      if (!matchId && !matchCat && !matchText) return false;
    }
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Header Banner */}
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
            <span style={{ fontSize: "1.25rem" }}>📜</span>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Moss Semantic Policy Registry
            </h2>
            <span
              style={{
                fontSize: "0.6875rem",
                padding: "0.125rem 0.5rem",
                borderRadius: "9999px",
                backgroundColor: "rgba(59, 130, 246, 0.1)",
                color: "var(--accent-blue)",
                border: "1px solid rgba(59, 130, 246, 0.3)",
                fontWeight: 600,
              }}
            >
              {policies.length} Policies Indexed
            </span>
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
              Policies available through the Moss runtime index (<code>{mossIndexName || "contextshield-security"}</code>); retrieval timing is reported per request when available.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            fontSize: "0.75rem",
            color: "var(--text-muted)",
          }}
        >
          <span>Runtime Status:</span>
          <strong style={{ color: mossStatus === "ready" ? "#10b981" : "#f59e0b" }}>
            {mossStatus === "ready" ? "Operational" : mossStatus || "Unknown"}
          </strong>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
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
        <input
          type="text"
          placeholder="Search by policy ID, category, or keyword..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            flex: 1,
            minWidth: "220px",
            padding: "0.375rem 0.75rem",
            borderRadius: "4px",
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-primary)",
            fontSize: "0.8125rem",
            outline: "none",
          }}
        />

        <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Severity:</span>
          {["all", "CRITICAL", "HIGH", "MEDIUM"].map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              style={{
                padding: "0.25rem 0.5rem",
                borderRadius: "4px",
                fontSize: "0.6875rem",
                fontWeight: severityFilter === s ? 600 : 400,
                backgroundColor: severityFilter === s ? "var(--bg-canvas)" : "transparent",
                color:
                  s === "CRITICAL"
                    ? "#ef4444"
                    : s === "HIGH"
                    ? "#f59e0b"
                    : severityFilter === s
                    ? "var(--text-primary)"
                    : "var(--text-secondary)",
                border: severityFilter === s ? "1px solid var(--border-strong)" : "1px solid transparent",
                cursor: "pointer",
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Policy Cards Grid */}
      <div className="policy-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "0.875rem" }}>
        {filtered.map((p) => {
          const isCrit = p.severity === "CRITICAL";
          const isHigh = p.severity === "HIGH";

          return (
            <div
              key={p.id}
              className="policy-card"
              style={{
                backgroundColor: "var(--bg-card)",
                borderRadius: "8px",
                padding: "1rem 1.125rem",
                border: "1px solid var(--border-subtle)",
                display: "flex",
                flexDirection: "column",
                gap: "0.625rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span
                  className="font-mono"
                  style={{
                    fontSize: "0.8125rem",
                    fontWeight: 700,
                    color: "var(--accent-blue)",
                  }}
                >
                  {p.id}
                </span>

                <div style={{ display: "flex", gap: "0.375rem" }}>
                  <span
                    style={{
                      fontSize: "0.625rem",
                      fontWeight: 700,
                      padding: "0.1rem 0.35rem",
                      borderRadius: "3px",
                      backgroundColor: isCrit ? "rgba(239, 68, 68, 0.12)" : isHigh ? "rgba(245, 158, 11, 0.12)" : "rgba(16, 185, 129, 0.12)",
                      color: isCrit ? "#ef4444" : isHigh ? "#f59e0b" : "#10b981",
                      border: `1px solid ${isCrit ? "rgba(239, 68, 68, 0.3)" : isHigh ? "rgba(245, 158, 11, 0.3)" : "rgba(16, 185, 129, 0.3)"}`,
                    }}
                  >
                    {p.severity}
                  </span>

                  <span
                    style={{
                      fontSize: "0.625rem",
                      fontWeight: 600,
                      padding: "0.1rem 0.35rem",
                      borderRadius: "3px",
                      backgroundColor: "var(--bg-canvas)",
                      color: "var(--text-secondary)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    Action: {p.recommended_action}
                  </span>
                </div>
              </div>

              <span
                style={{
                  fontSize: "0.6875rem",
                  color: "var(--text-muted)",
                  textTransform: "uppercase",
                  letterSpacing: "0.02em",
                }}
              >
                Category: {p.category}
              </span>

              <p
                style={{
                  fontSize: "0.8125rem",
                  color: "var(--text-secondary)",
                  lineHeight: 1.45,
                }}
              >
                {p.text}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
