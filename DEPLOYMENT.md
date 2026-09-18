# ContextShield — Production Deployment Guide

## 1. System Architecture

ContextShield is an enterprise-grade, zero-latency security gateway protecting downstream autonomous AI agents and live voice pipelines from untrusted external context, prompt injections, and data exfiltration.

```text
               +----------------------------------+
               |        Hackathon Judges / UI     |
               +----------------------------------+
                                | HTTPS
                                v
               +----------------------------------+
               |         Vercel (Frontend)        |
               |      Next.js 16 + Turbopack      |
               |    /api/contextshield/* proxies  |
               +----------------------------------+
                                | HTTPS
                                v
               +----------------------------------+
               |        Railway (Backend)         |
               |     FastAPI / Python Gateway     |
               |    Entrypoint: backend.app.main  |
               +----------------------------------+
                    |             |            |
                    v             v            v
             +------------+ +------------+ +------------+
             |    Moss    | |   Gemini   | | Protected  |
             | Local RT / | | Evaluator  | | AI Agent   |
             |  Policies  | | (Fallback) | | (Consumer) |
             +------------+ +------------+ +------------+
                                ^
                                | HTTPS
               +----------------------------------+
               |    LiveKit Cloud Agent Worker    |
               |     contextshield-voice worker   |
               +----------------------------------+
                                ^
                                | WebRTC
               +----------------------------------+
               |          LiveKit Cloud           |
               |       (Real-Time Audio STT)      |
               +----------------------------------+
```

---

## 2. Production Services Overview

| Component | Platform | Technology | Deployment Artifact / Config |
| :--- | :--- | :--- | :--- |
| **Frontend** | **Vercel** | Next.js 16 (App Router), TypeScript | `frontend/` directory, `package.json` |
| **Backend** | **Railway** | FastAPI, Uvicorn, Python 3.10+ | `railway.toml`, `Procfile`, `requirements.txt` |
| **Voice Worker** | **LiveKit Cloud** | Python `livekit-agents` worker | `livekit.toml`, `Dockerfile`, `livekit_voice/agent.py` |

---

## 3. Required Production Environment Variables

> [!IMPORTANT]
> **Zero Secrets Policy**: Never commit real secret values into git, Dockerfiles, or client-side bundles. Configure all values directly in the cloud provider's environment settings.

### A. Railway (FastAPI Backend)
| Variable Name | Description | Example / Allowed Values |
| :--- | :--- | :--- |
| `PORT` | Bound port assigned automatically by Railway | `${PORT}` (e.g. 8000) |
| `MOSS_PROJECT_ID` | Moss project UUID | UUID string |
| `MOSS_PROJECT_KEY` | Moss confidential project access key | Key string |
| `MOSS_INDEX_NAME` | Target security index | `contextshield-security` |
| `GEMINI_API_KEY` | Google Gemini API key for fallback evaluation & protected agent | API key string |
| `GEMINI_MODEL` | Target Gemini model | `gemini-3.6-flash` |
| `LLM_TARGET_LATENCY_MS` | Target evaluation timeout | `800` |
| `LLM_HARD_TIMEOUT_MS` | Hard evaluation timeout | `1500` |

### B. Vercel (Next.js Dashboard)
| Variable Name | Description | Example / Target Value |
| :--- | :--- | :--- |
| `CONTEXTSHIELD_BACKEND_URL` | Public HTTPS base URL of the deployed Railway backend | `https://<railway-app-name>.up.railway.app` |

### C. LiveKit Cloud Agent (Voice Worker)
| Variable Name | Description | Example / Target Value |
| :--- | :--- | :--- |
| `LIVEKIT_URL` | Cloud WebRTC WebSocket endpoint | `wss://<project-subdomain>.livekit.cloud` |
| `LIVEKIT_API_KEY` | LiveKit API Key | Key string |
| `LIVEKIT_API_SECRET` | LiveKit API Secret | Secret string |
| `CONTEXTSHIELD_API_URL` | Public HTTPS URL of Railway backend | `https://<railway-app-name>.up.railway.app` |
| `LIVEKIT_STT_MODEL` | Deepgram speech-to-text model | `deepgram/nova-3` |
| `LIVEKIT_STT_LANGUAGE` | Language code for STT | `en` |

---

## 4. Local Development Commands

### Backend
```bash
# Start backend locally on port 8000
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Frontend
```bash
# Start development server on port 3000
cd frontend
npm run dev

# Or build and run production server locally
npm run build
npm run start -- -p 3000
```

### LiveKit Voice Worker
```bash
# Run local worker in development mode (connects to LiveKit Cloud room)
python -m livekit_voice.agent dev
```

---

## 5. Production Build & Test Commands

```bash
# Run full backend regression suite (108 tests)
python -m pytest -v

# Run frontend production build validation
cd frontend
npm run build
```

---

## 6. Health & Telemetry Verification Endpoints

Public production endpoints to verify system health without secret exposure:

- `GET /v1/shield/health`: Verifies gateway status (`{"status": "ok"}`) and Moss index status.
- `GET /v1/shield/dashboard/health`: Verifies operational telemetry across gateway, Moss, Gemini, and LiveKit.
- `GET /v1/shield/dashboard/stats`: Returns current session aggregate stats.
- `GET /v1/shield/dashboard/events`: Returns privacy-safe audit trail (no raw transcripts or secret leaks).
- `GET /v1/shield/dashboard/policies`: Dynamic catalog of security policies loaded from Moss runtime.
- `POST /v1/shield/demo/protected-agent`: Runs untrusted context through ContextShield and returns protected agent execution status.

---

## 7. Step-by-Step Deployment Workflow

### Step 1: Deploy Backend to Railway
1. Go to [railway.com](https://railway.com) and create a new project from your GitHub repository (or via Railway CLI: `railway up`).
2. Railway detects `railway.toml` and starts the app with:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
3. In Railway **Variables**, add:
   - `MOSS_PROJECT_ID`
   - `MOSS_PROJECT_KEY`
   - `MOSS_INDEX_NAME`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL=gemini-3.6-flash`
4. Under **Settings > Networking**, generate a public domain (e.g. `https://contextshield-backend.up.railway.app`).
5. Verify health:
   ```bash
   curl -s https://<railway-domain>/v1/shield/health
   ```

### Step 2: Deploy Frontend to Vercel
1. Go to [vercel.com](https://vercel.com) and import the repository.
2. Set **Root Directory** to `frontend`.
3. Under **Environment Variables**, add:
   - `CONTEXTSHIELD_BACKEND_URL=https://<railway-domain>`
4. Click **Deploy**. Vercel will build with `npm run build` and assign an HTTPS URL (e.g. `https://contextshield.vercel.app`).
5. Open the dashboard in browser. Verify that the header shows: `● Gateway Operational`.

### Step 3: Deploy Voice Worker to LiveKit Cloud
1. In `livekit_voice/`:
   ```bash
   lk agent deploy --secrets "CONTEXTSHIELD_API_URL=https://<railway-domain>"
   ```
2. Check agent status:
   ```bash
   lk agent status
   ```
3. Test a voice turn using microphone in LiveKit Agent Sandbox or via browser client.

---

## 8. Common Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **"Backend Unavailable" banner on dashboard** | `CONTEXTSHIELD_BACKEND_URL` is unset or points to an offline URL | Verify Railway URL in Vercel environment variables and ensure Railway deployment is active. |
| **Moss status "not_configured"** | Missing `MOSS_PROJECT_ID` or `MOSS_PROJECT_KEY` | Add environment variables in Railway project settings. |
| **Gemini rate_limited status** | Free tier quota reached | Evaluator falls back safely to deterministic rules and Moss policies without blocking legitimate traffic. |
| **LiveKit worker not receiving jobs** | Worker offline or mismatched `LIVEKIT_URL` | Check LiveKit Cloud console for active worker registration in the target region. |
