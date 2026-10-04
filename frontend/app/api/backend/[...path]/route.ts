import { NextRequest, NextResponse } from "next/server";

// Only the existing public model/scenario endpoints are forwarded. No cookies or credentials.
async function forward(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const endpoint = path.join("/");
  const allowed =
    /^(analytics\/(?:defaults|sensitivity|simulation)|defaults|evaluate|compare|scenarios(?:\/[0-9a-f-]{36}(?:\/evaluation)?)?)$/.test(
      endpoint,
    );
  if (!allowed)
    return NextResponse.json(
      { detail: "Unknown application endpoint" },
      { status: 404 },
    );
  const origin = request.headers.get("origin");
  // Next may normalize the internal URL to localhost; compare the browser-facing Host.
  const expectedOrigin = `${request.nextUrl.protocol}//${request.headers.get("host")}`;
  if (request.method !== "GET" && origin && origin !== expectedOrigin) {
    return NextResponse.json(
      { detail: "Cross-origin changes are not allowed" },
      { status: 403 },
    );
  }
  try {
    const url = new URL(
      `/api/v1/${endpoint}`,
      process.env.BACKEND_URL || "http://127.0.0.1:8000",
    );
    url.search = request.nextUrl.search;
    const response = await fetch(url, {
      method: request.method,
      headers: { "Content-Type": "application/json" },
      body: request.method === "GET" ? undefined : await request.text(),
      cache: "no-store",
      signal: AbortSignal.timeout(
        endpoint.startsWith("analytics/") ? 60000 : 15000,
      ),
      redirect: "error",
    });
    if (response.status >= 500)
      return NextResponse.json(
        {
          detail:
            "The calculation or storage service is unavailable. Your edits are still here. Please retry.",
        },
        { status: 503 },
      );
    return new NextResponse(
      response.status === 204 ? null : await response.text(),
      {
        status: response.status,
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-store",
        },
      },
    );
  } catch {
    return NextResponse.json(
      {
        detail:
          "Cannot connect to the modelling service. Check that the backend is running, then retry.",
      },
      { status: 503 },
    );
  }
}
export const GET = forward;
export const POST = forward;
export const PUT = forward;

export const DELETE = forward;
