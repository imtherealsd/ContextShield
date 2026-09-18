import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.CONTEXTSHIELD_BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await fetch(`${BACKEND_URL}/v1/shield/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: "Backend unavailable", message: err.message },
      { status: 503 }
    );
  }
}
