"use client";

import React from "react";

export function ArchitectureView() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Overview Banner */}
      <div
        style={{
          padding: "1.25rem 1.5rem",
          borderRadius: "8px",
          backgroundColor: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "1.25rem" }}>📐</span>
          <h2 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)" }}>
            ContextShield System Architecture
          </h2>
        </div>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
          ContextShield operates as a zero-latency firewall for autonomous AI agents. By combining deterministic token scanning with local in-memory semantic retrieval via the Moss Local Runtime, over 95% of incoming context is resolved in &lt; 5ms without calling costly external LLM APIs.
        </p>
      </div>

      {/* Visual Pipeline Flow Chart */}
      <div
        style={{
          backgroundColor: "var(--bg-card)",
          borderRadius: "8px",
          padding: "1.5rem",
          border: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
        }}
      >
        <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)" }}>
          End-to-End Zero-Latency Pipeline Flow
        </h3>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {/* Layer 1: Ingestion Channels */}
          <div
            style={{
              padding: "1rem",
              borderRadius: "6px",
              backgroundColor: "var(--bg-canvas)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-blue)", marginBottom: "0.5rem" }}>
              [LAYER 1] UNTRUSTED INGESTION SOURCES
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "0.5rem" }}>
              <div style={{ padding: "0.5rem", borderRadius: "4px", backgroundColor: "var(--bg-card)", border: "1px solid var(--border-subtle)", fontSize: "0.75rem" }}>
                🎙️ <strong>LiveKit Voice</strong><br /><span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>deepgram/nova-3 STT</span>
              </div>
              <div style={{ padding: "0.5rem", borderRadius: "4px", backgroundColor: "var(--bg-card)", border: "1px solid var(--border-subtle)", fontSize: "0.75rem" }}>
                🌐 <strong>Web Context</strong><br /><span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Scrapers & search data</span>
              </div>
              <div style={{ padding: "0.5rem", borderRadius: "4px", backgroundColor: "var(--bg-card)", border: "1px solid var(--border-subtle)", fontSize: "0.75rem" }}>
                🔌 <strong>API Payloads</strong><br /><span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Webhook & integrations</span>
              </div>
              <div style={{ padding: "0.5rem", borderRadius: "4px", backgroundColor: "var(--bg-card)", border: "1px solid var(--border-subtle)", fontSize: "0.75rem" }}>
                📄 <strong>Documents</strong><br /><span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>RAG & PDF uploads</span>
              </div>
            </div>
          </div>

          <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>↓</div>

          {/* Layer 2: Schema Gateway & Deterministic Scanner */}
          <div
            style={{
              padding: "1rem",
              borderRadius: "6px",
              backgroundColor: "var(--bg-canvas)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#10b981", marginBottom: "0.5rem" }}>
              [LAYER 2] DETERMINISTIC PRE-FILTERING (~1-2 ms)
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              SchemaGateway validates strict bounds and creates dual analysis buffers (normalized text + preserved raw zero-width characters). Deterministic Threat Scanner executes compiled regex rules detecting prompt injections, secret exfiltration headers, and evasion techniques.
            </p>
          </div>

          <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>↓</div>

          {/* Layer 3: Moss Local Runtime Semantic Retrieval */}
          <div
            style={{
              padding: "1rem",
              borderRadius: "6px",
              backgroundColor: "var(--bg-canvas)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#8b5cf6", marginBottom: "0.5rem" }}>
              [LAYER 3] MOSS LOCAL RUNTIME SEMANTIC POLICIES (~2-4 ms)
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              Queries local in-memory HNSW index (<code>contextshield-security</code>) via the official Moss SDK. Zero network hops. Maps semantically similar corporate security policies (e.g. POL-001 instruction override, POL-003 credential exfiltration) to strengthen evidence.
            </p>
          </div>

          <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>↓</div>

          {/* Layer 4: Deterministic Risk Engine & Gating */}
          <div
            style={{
              padding: "1rem",
              borderRadius: "6px",
              backgroundColor: "var(--bg-canvas)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#f59e0b", marginBottom: "0.5rem" }}>
              [LAYER 4] DETERMINISTIC RISK ENGINE (ZERO-LATENCY GATE)
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              Evaluates deterministic findings and Moss alignment. <strong>Critical rules have absolute authority</strong>: overrides, key leaks, and destructive commands immediately trigger BLOCK (or SANITIZE if isolated). Clean documentation immediately resolves to SAFE.
            </p>
          </div>

          <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
            Is Context Genuinely Ambiguous?
          </div>

          {/* Layer 5: Fork Branch */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            {/* NO: Fast Path */}
            <div
              style={{
                padding: "1rem",
                borderRadius: "6px",
                backgroundColor: "rgba(16, 185, 129, 0.08)",
                border: "1px solid rgba(16, 185, 129, 0.25)",
              }}
            >
              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#10b981", marginBottom: "0.25rem" }}>
                NO (&gt;95% of requests)
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                <strong>Fast Path (~3-5ms total)</strong>. LLM is completely bypassed. Immediate SAFE, SANITIZE, or BLOCK decision returned. Zero API costs.
              </p>
            </div>

            {/* YES: Gemini Fallback */}
            <div
              style={{
                padding: "1rem",
                borderRadius: "6px",
                backgroundColor: "rgba(245, 158, 11, 0.08)",
                border: "1px solid rgba(245, 158, 11, 0.25)",
              }}
            >
              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#f59e0b", marginBottom: "0.25rem" }}>
                YES (&lt;5% ambiguous edge cases)
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                <strong>Gemini Context Evaluator</strong> invoked with strict structured JSON output and hard timeout. Fails secure to REVIEW on timeout or rate limit.
              </p>
            </div>
          </div>

          <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>↓</div>

          {/* Final Delivery */}
          <div
            style={{
              padding: "1rem",
              borderRadius: "6px",
              backgroundColor: "var(--bg-canvas)",
              border: "1px solid var(--border-strong)",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
              🤖 DOWNSTREAM PROTECTED AGENT
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              SAFE: Delivered • SANITIZE: Delivered (Hostile Scrubbed) • REVIEW / BLOCK: <strong>NULL (NO CONTEXT DELIVERED)</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
