import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.CONTEXTSHIELD_BACKEND_URL || "http://127.0.0.1:8000";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const limit = searchParams.get("limit") || "50";
    const source = searchParams.get("source") || "";
    const decision = searchParams.get("decision") || "";

    const query = new URLSearchParams();
    query.set("limit", limit);
    if (source) query.set("source", source);
    if (decision) query.set("decision", decision);

    const res = await fetch(`${BACKEND_URL}/v1/shield/dashboard/events?${query.toString()}`, {
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
      { error: "Backend unavailable", message },
      { status: 503 }
    );
  }
}
