# ContextShield — Pre-Recording & Demo Reset Checklist

Follow this checklist before starting the screen capture for the 2-minute demonstration video.

---

## 1. Cloud Service Verification

- [ ] **Vercel Dashboard Online**: Navigate to `https://frontend-sigma-green-56.vercel.app`. Verify that the top header shows `● Gateway Operational` with a green status indicator.
- [ ] **Railway Backend Healthy**: Verify `GET https://contextshield-production.up.railway.app/v1/shield/health` returns `{"status": "ok"}` (HTTP 200).
- [ ] **LiveKit Cloud Worker Active**: Verify that the cloud agent worker `contextshield-voice` is running in LiveKit Cloud (region `ap-south`).
- [ ] **Protected Agent Responding**: Run a quick test in the **Protected Agent Boundary** tab to ensure responses return smoothly (~0.5s).

---

## 2. Browser & Display Setup

- [ ] **Resolution**: Set display resolution to **1920 × 1080** (16:9 aspect ratio).
- [ ] **Browser Zoom**: Set Google Chrome / browser zoom to **110%** (ensures all table text, badges, and metrics are crisp and readable on mobile/video players).
- [ ] **Clean Browser Window**:
  - Close all other browser tabs, developer tools, and extensions.
  - Hide the browser bookmarks bar (`Ctrl+Shift+B`).
  - Use a dedicated, clean browser profile with personal account icons or emails hidden.
- [ ] **Theme**: Ensure the dashboard is set to the default sleek dark mode (`data-theme="dark"`).

---

## 3. Desktop & Audio Environment

- [ ] **Notifications Disabled**: Turn on Windows "Do Not Disturb" / Focus Assist to suppress system notifications.
- [ ] **Clean Desktop**: Close all local terminal windows, code editors, or taskbars containing file paths or sensitive keys.
- [ ] **Microphone Level**: Set microphone gain so voiceover is crisp, clear, and free of background noise or clipping.

---

## 4. Rehearsal Walkthrough (1m 52s Pace)

1. **Shot 1 (0:00 – 0:12)**: Overview tab overview — gentle downward glance.
2. **Shot 2 & 3 (0:12 – 0:48)**: Pipeline Architecture tab — trace the path from sources to Protected Agent.
3. **Shot 4 (0:48 – 1:12)**: Protected Agent Boundary — run Scenario 3 (Prompt Injection) $\rightarrow$ pause on `NO CONTEXT DELIVERED`.
4. **Shot 5 (1:12 – 1:30)**: Protected Agent Boundary — run Scenario 2 (Sanitization) $\rightarrow$ highlight clean context.
5. **Shot 6 (1:30 – 1:45)**: LiveKit Voice tab — show real-time voice block turn.
6. **Shot 7 (1:45 – 1:56)**: Overview tab — concluding summary and URL callout.

---

## 5. Contingency Plan

- If an API request is delayed during recording, do not rush or switch to terminal debugging. Stop the recording take, refresh the browser, and restart the take from the beginning.
- The production system has been verified with 100% test passing rates; clean takes take less than two minutes.
