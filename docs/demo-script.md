# ContextShield — 2-Minute Hackathon Demo Script

- **Target Video Duration**: 1 minute 52 seconds (Safety margin: 8 seconds below 2:00 ceiling)
- **Total Spoken Word Count**: 223 words
- **Pacing**: Steady, deliberate, authoritative (~130 words/minute)
- **Primary Objective**: Visually prove that downstream AI agents never receive raw, blocked, or review-required external context.

---

## Script & Cue Sheet

| Time | Section | Screen & Action | Voiceover Narration | Visual Focus |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 – 0:12** | **Hook / Problem** | Start on deployed Vercel Dashboard (**Overview** tab). Light slow scroll past real-time metric cards. | *"AI agents increasingly consume content from websites, APIs, documents, and voice transcripts. But those untrusted sources can embed prompt injections designed to hijack the agent before it even starts reasoning."* | Operational status banner: `● Gateway Operational`, 4 Decision metric cards. |
| **0:12 – 0:28** | **What ContextShield Does** | Click **Pipeline Architecture** tab. Mermaid pipeline diagram is visible. | *"ContextShield is a low-latency security gateway that moves the trust decision in front of the agent. The agent never consumes raw external context directly — only verified, approved context."* | The upstream gateway position intercepting data before the Protected Agent. |
| **0:28 – 0:48** | **Architecture & Moss** | Mouse hovers over parallel Scanner and Moss Retrieval blocks, then over Gated Gemini block. | *"Our pipeline combines high-speed deterministic scanning with Moss semantic retrieval over twenty enterprise security policies. Clear threats and safe inputs resolve immediately on the fast path, while Gemini is gated only for ambiguous cases."* | Parallel Scanner + Moss block; separate Gated Evaluator vs. Downstream Agent boxes. |
| **0:48 – 1:12** | **Live BLOCK Attack (Core Proof)** | Click **Protected Agent Boundary** tab. Select Preset 3 (Prompt Injection). Click **Evaluate & Run Protected Agent**. | *"Let's see it live on our production deployment. Here, an incoming document contains an instruction override seeking API keys. ContextShield detects the threat in sub-milliseconds and issues a BLOCK verdict. Notice the boundary status: No Context Delivered. The downstream agent is never invoked."* | Red badge: **`BLOCK`** (Risk 95.0), **`NO CONTEXT DELIVERED`**, and `Agent Called: false`. |
| **1:12 – 1:30** | **Sanitize & Clean Context** | Select Preset 2 (Sanitization). Click **Evaluate & Run Protected Agent**. | *"When an attack is embedded inside useful documentation, ContextShield sanitizes it. The injection is stripped, the payload is verified clean, and only the sanitized context reaches the agent to safely answer the user's question."* | **`SANITIZE`** badge, clean documentation with `[SANITIZED_UNTRUSTED_INSTRUCTION]` marker, downstream agent answering successfully. |
| **1:30 – 1:45** | **LiveKit Voice Security** | Click **LiveKit Voice** tab. Show production voice turn table. Click the BLOCK voice event. | *"This same boundary protects real-time voice. LiveKit transcribes the audio turn, ContextShield evaluates the transcript against our Railway backend, and unsafe speech is blocked before it reaches the agent."* | `Source: LiveKit Voice`, `Decision: BLOCK`, Voice-to-decision latency (~0.4ms), `NO CONTEXT DELIVERED`. |
| **1:45 – 1:55** | **Ending & Vision** | Switch back to **Overview** tab. | *"By intercepting untrusted context before ingestion, ContextShield gives autonomous agents a strict security boundary: inspect first, trust second."* | Final view of clean system health, Moss policy count (20), and zero credential leaks. |
| **1:55 – 1:58** | **Outro Card** | Static final frame or hold on Overview tab. | *(Silence / 3-second buffer)* | URL text on screen: `https://frontend-sigma-green-56.vercel.app` |

---

## Speaking Notes & Delivery Rules
1. **Never use hype terms**: Do not say *"revolutionary"*, *"unhackable"*, or *"100% secure"*.
2. **Never claim literal 0ms**: Use *"sub-millisecond"*, *"fast deterministic path"*, or *"low-latency"*.
3. **Keep mouse movements deliberate**: Move smoothly between tabs without nervous hovering or sudden scrolling.
4. **Pause at 1:04**: Leave a clear 2-second visual pause on **`NO CONTEXT DELIVERED`** — this is the critical architectural takeaway judges look for.
