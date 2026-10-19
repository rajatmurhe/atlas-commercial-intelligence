import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "node:crypto";
import { backendIdentityHeaders } from "@/lib/cloud-auth";

export const runtime = "nodejs";
const allowed = new Set([
  "overview",
  "chat",
  "quality",
  "analysis",
  "feedback",
  "briefs",
]);

async function proxy(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  if (path.length !== 1 || !allowed.has(path[0]))
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  if (req.method === "POST") {
    const origin = req.headers.get("origin");
    const expectedOrigin =
      process.env.APP_ORIGIN ||
      `${req.nextUrl.protocol}//${req.headers.get("host")}`;
    if (!origin || origin !== expectedOrigin)
      return NextResponse.json(
        { detail: "Invalid request origin" },
        { status: 403 },
      );
  }
  const key = process.env.API_KEY;
  if (!key)
    return NextResponse.json(
      { detail: "Server configuration is incomplete. Run local setup." },
      { status: 503 },
    );
  const existing = req.cookies.get("ciq_session")?.value;
  const session =
    existing && /^[0-9a-f-]{36}$/.test(existing) ? existing : randomUUID();
  const url = new URL(
    `/api/${path[0]}`,
    process.env.BACKEND_URL || "http://127.0.0.1:8031",
  );
  req.nextUrl.searchParams.forEach((value, name) =>
    url.searchParams.set(name, value),
  );
  if (path[0] === "briefs" && req.method === "GET")
    url.searchParams.set("session_id", session);
  try {
    let body;
    if (req.method === "POST") {
      const raw = await req.text();
      if (raw.length > 10000)
        return NextResponse.json(
          { detail: "Request is too large" },
          { status: 413 },
        );
      body = JSON.stringify({ ...JSON.parse(raw), session_id: session });
    }
    const response = await fetch(url, {
      method: req.method,
      headers: {
        "X-API-Key": key,
        ...(await backendIdentityHeaders()),
        "Content-Type": "application/json",
      },
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(45000),
    });
    const result = NextResponse.json(await response.json(), {
      status: response.status,
    });
    result.cookies.set("ciq_session", session, {
      httpOnly: true,
      sameSite: "strict",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 7,
    });
    result.headers.set("Cache-Control", "no-store");
    return result;
  } catch {
    return NextResponse.json(
      {
        detail:
          "The analysis service is unavailable. Check that the backend is running.",
      },
      { status: 503 },
    );
  }
}
export const GET = proxy;
export const POST = proxy;
