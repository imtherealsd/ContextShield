"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header, HealthData } from "./components/Header";
import { Navigation, TabKey } from "./components/Navigation";
import { MetricsOverview, DashboardStats } from "./components/MetricsOverview";
import { LiveFeed } from "./components/LiveFeed";
import { VoicePanel, VoiceTurnEvent } from "./components/VoicePanel";
import { ProtectedAgentView } from "./components/ProtectedAgentView";
import { PoliciesView, PolicyItem } from "./components/PoliciesView";
import { ArchitectureView } from "./components/ArchitectureView";
import { EventDrawer, SecurityEvent } from "./components/EventDrawer";
import { SimulateThreatModal } from "./components/SimulateThreatModal";

export default function DashboardPage() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  // Telemetry States
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [voiceTurns, setVoiceTurns] = useState<VoiceTurnEvent[]>([]);
  const [policies, setPolicies] = useState<PolicyItem[]>([]);
  const [mossIndexName, setMossIndexName] = useState<string>("contextshield-security");
  const [mossStatus, setMossStatus] = useState<string>("ready");
  const [health, setHealth] = useState<HealthData | null>(null);
  const [backendAvailable, setBackendAvailable] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null);
  const [isSimulateOpen, setIsSimulateOpen] = useState<boolean>(false);

  // Theme Toggle
  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

  // Primary Data Fetcher
  const fetchData = useCallback(async () => {
    try {
      setRefreshing(true);
      const [statsRes, eventsRes, voiceRes, polRes, healthRes] = await Promise.all([
        fetch("/api/contextshield/stats"),
        fetch("/api/contextshield/events?limit=50"),
        fetch("/api/contextshield/voice-turns?limit=50"),
        fetch("/api/contextshield/policies"),
        fetch("/api/contextshield/health"),
      ]);

      if (healthRes.ok) {
        setHealth(await healthRes.json());
        setBackendAvailable(true);
      } else {
        setBackendAvailable(false);
      }

      if (statsRes.ok) setStats(await statsRes.json());
      if (eventsRes.ok) setEvents(await eventsRes.json());
      if (voiceRes.ok) setVoiceTurns(await voiceRes.json());
      if (polRes.ok) {
        const polData = await polRes.json();
        setPolicies(polData.policies || []);
        setMossIndexName(polData.moss_index_name || "contextshield-security");
        setMossStatus(polData.moss_status || "ready");
      }
    } catch (err) {
      console.warn("Telemetry fetch error (backend may be warming up):", err);
      setBackendAvailable(false);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Poll every 1.5 seconds for real-time responsiveness
  useEffect(() => {
    let mounted = true;
    const timer = setTimeout(() => {
      if (mounted) {
        void fetchData();
      }
    }, 0);
    const interval = setInterval(() => {
      if (mounted) {
        void fetchData();
      }
    }, 1500);
    return () => {
      mounted = false;
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [fetchData]);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top Header */}
      <Header
        health={health}
        theme={theme}
        onToggleTheme={toggleTheme}
        onOpenSimulate={() => setIsSimulateOpen(true)}
        refreshing={refreshing}
        onRefresh={fetchData}
        backendAvailable={backendAvailable}
      />

      {/* Backend Unavailable Banner */}
      {!backendAvailable && (
        <div
          style={{
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            borderBottom: "1px solid rgba(239, 68, 68, 0.3)",
            padding: "0.75rem 1.5rem",
            color: "#ef4444",
            fontSize: "0.8125rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "0.5rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span>⚠️</span>
            <strong>Backend Unavailable:</strong>
            <span>Unable to connect to ContextShield security gateway. No synthetic or fake metrics are displayed.</span>
          </div>
          <button
            onClick={fetchData}
            style={{
              background: "transparent",
              border: "1px solid #ef4444",
              borderRadius: "4px",
              color: "#ef4444",
              padding: "0.2rem 0.6rem",
              fontSize: "0.75rem",
              cursor: "pointer",
            }}
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <Navigation
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        eventCount={events.length}
        voiceCount={voiceTurns.length}
        policyCount={policies.length}
      />

      {/* Main Workspace Area */}
      <main
        className="dashboard-main"
        style={{
          flex: 1,
          padding: "1.5rem",
          maxWidth: "1440px",
          width: "100%",
          margin: "0 auto",
        }}
      >
        {activeTab === "overview" && (
          <div className="overview-stack" style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
            <section className="boundary-strip" aria-label="ContextShield security boundary">
              <div className="boundary-stage">
                <span className="boundary-stage-label">UNTRUSTED CONTEXT</span>
                <strong className="boundary-stage-title">Web · API · Docs · Voice</strong>
                <span className="boundary-stage-detail">External inputs enter unverified.</span>
              </div>
              <span className="boundary-arrow" aria-hidden="true">→</span>
              <div className="boundary-stage" style={{ borderColor: "rgba(59, 130, 246, 0.35)" }}>
                <span className="boundary-stage-label" style={{ color: "var(--accent-blue)" }}>CONTEXTSHIELD</span>
                <strong className="boundary-stage-title">Inspect · Retrieve · Decide</strong>
                <span className="boundary-stage-detail">Deterministic security gateway.</span>
              </div>
              <span className="boundary-arrow" aria-hidden="true">→</span>
              <div className="boundary-stage" style={{ borderColor: "rgba(16, 185, 129, 0.35)" }}>
                <span className="boundary-stage-label" style={{ color: "var(--badge-safe-text)" }}>PROTECTED AGENT</span>
                <strong className="boundary-stage-title">Approved Context Only</strong>
                <span className="boundary-stage-detail">SAFE · SANITIZE · REVIEW · BLOCK</span>
              </div>
            </section>
            <MetricsOverview stats={stats} />
            <div>
              <div className="section-heading-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h3 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Recent Ingestion Stream (Latest Events)
                </h3>
                <button
                  onClick={() => setActiveTab("feed")}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--accent-blue)",
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  View Full Feed ({events.length}) →
                </button>
              </div>
              <LiveFeed
                events={events.slice(0, 5)}
                onSelectEvent={setSelectedEvent}
                loading={loading}
              />
            </div>
          </div>
        )}

        {activeTab === "feed" && (
          <LiveFeed
            events={events}
            onSelectEvent={setSelectedEvent}
            loading={loading}
          />
        )}

        {activeTab === "voice" && (
          <VoicePanel
            voiceTurns={voiceTurns}
            onSelectEvent={setSelectedEvent}
          />
        )}

        {activeTab === "boundary" && (
          <ProtectedAgentView events={events} />
        )}

        {activeTab === "policies" && (
          <PoliciesView
            policies={policies}
            mossIndexName={mossIndexName}
            mossStatus={mossStatus}
          />
        )}

        {activeTab === "architecture" && (
          <ArchitectureView />
        )}
      </main>

      {/* Slide-over Detail Drawer */}
      <EventDrawer
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />

      {/* Simulate Threat Ingestion Modal */}
      <SimulateThreatModal
        isOpen={isSimulateOpen}
        onClose={() => setIsSimulateOpen(false)}
        onSuccess={() => {
          fetchData();
        }}
      />
    </div>
  );
}
