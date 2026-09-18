"use client";

import React from "react";

export type TabKey = "overview" | "feed" | "voice" | "boundary" | "policies" | "architecture";

interface NavigationProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  eventCount: number;
  voiceCount: number;
  policyCount: number;
}

export function Navigation({
  activeTab,
  onSelectTab,
  eventCount,
  voiceCount,
  policyCount,
}: NavigationProps) {
  const tabs: { key: TabKey; label: string; count?: number; icon: string }[] = [
    { key: "overview", label: "Overview", icon: "📊" },
    { key: "feed", label: "Live Security Feed", count: eventCount, icon: "⚡" },
    { key: "voice", label: "LiveKit Voice", count: voiceCount, icon: "🎙️" },
    { key: "boundary", label: "Protected Agent Boundary", icon: "🛡️" },
    { key: "policies", label: "Moss Policy Registry", count: policyCount, icon: "📜" },
    { key: "architecture", label: "Pipeline Architecture", icon: "📐" },
  ];

  return (
    <nav
      style={{
        borderBottom: "1px solid var(--border-subtle)",
        backgroundColor: "var(--bg-card)",
        padding: "0 1.5rem",
        display: "flex",
        alignItems: "center",
        gap: "0.25rem",
        overflowX: "auto",
        scrollbarWidth: "none",
      }}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;
        return (
          <button
            key={tab.key}
            id={`nav-tab-${tab.key}`}
            onClick={() => onSelectTab(tab.key)}
            style={{
              padding: "0.875rem 1rem",
              backgroundColor: "transparent",
              border: "none",
              borderBottom: isActive ? "2px solid var(--accent-blue)" : "2px solid transparent",
              color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
              fontSize: "0.875rem",
              fontWeight: isActive ? 600 : 500,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              whiteSpace: "nowrap",
              transition: "all 0.15s ease",
            }}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                style={{
                  fontSize: "0.6875rem",
                  padding: "0.125rem 0.375rem",
                  borderRadius: "9999px",
                  backgroundColor: isActive ? "var(--accent-blue)" : "var(--bg-canvas)",
                  color: isActive ? "#ffffff" : "var(--text-muted)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
