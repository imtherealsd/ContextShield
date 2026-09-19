# ContextShield — Final Production Demonstration Script (Synchronized)

- **Silent Master Duration**: 114.92 seconds (WebM)
- **Narrated Master Duration**: 113.92 seconds (MP4, H.264 / AAC)
- **Target Duration Window**: 1 minute 50 seconds to 1 minute 58 seconds (Ceiling: 2:00 / 120s)
- **Total Spoken Word Count**: 192 words
- **Pacing**: Steady, deliberate, authoritative (~130 words/minute)
- **Production URL Recorded**: `https://frontend-sigma-green-56.vercel.app`
- **Resolution**: 1920x1080 (16:9 widescreen)

---

## Cue Sheet & Exact Narration

| Shot | Time Range | Screen & User Action | Spoken Narration | Visual Focus |
| :--- | :--- | :--- | :--- | :--- |
| **SHOT 1** | **0:00 – 0:12** | Starts on **Overview** tab. Cursor smoothly inspects Gateway Operational status and metric cards. | *"AI agents consume untrusted data from documents, APIs, and voice. Without an external gateway, prompt injections hijack reasoning before execution begins."* | Operational status indicator (`● Gateway Operational`), Decision cards. |
| **SHOT 2** | **0:12 – 0:48** | Switched to **Pipeline Architecture** tab. Cursor moves through Untrusted Context, Scanner + Moss, Risk Engine, and Gated Gemini. | *"ContextShield is a low-latency security gateway positioned in front of the agent. Inbound context is scanned in parallel by sub-millisecond deterministic rules and Moss semantic retrieval over enterprise policies. Clear threats and safe inputs resolve immediately, while Gemini is gated behind the deterministic path for ambiguous cases. Downstream agents are strictly isolated from unapproved context."* | Parallel Scanner + Moss block; separate Gated Evaluator vs. Downstream Agent boxes. |
| **SHOT 3** | **0:48 – 1:12** | Switched to **Protected Agent Boundary** tab. Preset 3 selected, **Run** clicked. **2.5s stationary pause** on result. | *"Here is our production proof. An inbound document delivers an instruction override seeking API keys. ContextShield detects the threat and issues a BLOCK. The protected agent was never called and received no context from the blocked request. Zero toxic tokens reach the model."* | **HERO MOMENT**: `BLOCK` badge (Risk 95.0), **`NO CONTEXT DELIVERED`**, `Agent Called: false`. |
| **SHOT 4** | **1:12 – 1:30** | Preset 2 (SANITIZE) selected, **Run** clicked. Result displays excised injection and downstream agent answer. | *"When an isolated malicious instruction is embedded in legitimate documentation, ContextShield sanitizes it. The hostile override is excised, the payload is revalidated, and only cleaned context reaches the agent."* | `SANITIZE` badge, `[SANITIZED_UNTRUSTED_INSTRUCTION]` marker, clean downstream agent response. |
| **SHOT 5** | **1:30 – 1:41** | Switched to **Live Security Feed** tab. Top `BLOCK` event clicked, opening event detail drawer. | *"In the audit drawer, we inspect the decision evidence: deterministic rule triggers, sub-millisecond latency, and semantic policy candidates retrieved by Moss."* | Event Drawer: `Applied Security Evidence` vs. `Retrieved Moss Policies`. |
| **SHOT 6** | **1:41 – 1:50** | Switched to **LiveKit Voice** tab. Verified production voice `BLOCK` event drawer opened. | *"The same boundary protects voice: LiveKit transcribes speech, and ContextShield blocks unsafe context before reaching the agent."* | `Source: LiveKit Voice`, `Decision: BLOCK`, voice turn latency, `NO CONTEXT DELIVERED`. |
| **SHOT 7** | **1:50 – 1:54** | Returned to **Overview** tab for clean branding hold. 1.0s clean ending silence. | *"ContextShield: inspect first, trust second."* | Final view of clean system health and brand banner. |

---

## Production Verification Metrics

- **Final Spoken Word Count**: 192 words
- **Actual Video Duration (Narrated MP4)**: 113.92 seconds
- **Actual Video Duration (Silent WebM)**: 114.92 seconds
- **Narration Pace**: 131 words/minute
- **Audio Ending Buffer**: 1.00 second of clean silence before video end
