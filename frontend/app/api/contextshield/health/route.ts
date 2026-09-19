import { NextResponse } from "next/server";

const BACKEND_URL = process.env.CONTEXTSHIELD_BACKEND_URL || "http://127.0.0.1:8000";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/v1/shield/dashboard/health`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: "Backend error", status: res.status },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      {
        gateway: "unavailable",
        error: message,
        moss: { status: "unknown", loaded: false },
        gemini: { configured: false, model: null, last_status: "unknown" },
        livekit: { last_voice_event_at: null, recent_activity: false },
      },
      { status: 503 }
    );
  }
}
