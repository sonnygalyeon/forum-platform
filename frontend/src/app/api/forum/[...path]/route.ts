import { NextResponse } from "next/server";
import { clearAuthCookies, currentTokens, djangoFetch, refreshAccess, setAuthCookies } from "@/lib/server-auth";

const ALLOWED_ROOTS = new Set(["publications", "feed", "communities", "notifications", "users", "comments", "admin", "moderation", "ready", "uploads", "identity", "search", "discover", "messenger", "observability"]);

type Context = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, context: Context) {
  const { path } = await context.params;
  if (!path.length || !ALLOWED_ROOTS.has(path[0])) {
    return NextResponse.json({ detail: "Endpoint is not exposed by the frontend proxy." }, { status: 404 });
  }

  const incomingUrl = new URL(request.url);
  const djangoPath = `${path.join("/")}/${incomingUrl.search}`;
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer();
  const headers = new Headers();
  const requestId = request.headers.get("x-request-id") || crypto.randomUUID();
  headers.set("X-Request-ID", requestId);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);

  const { access, refresh } = await currentTokens();
  let currentAccess = access;
  let rotatedRefresh: string | undefined;
  let upstream = await djangoFetch(djangoPath, { method: request.method, headers, body }, currentAccess);

  if (upstream.status === 401 && refresh) {
    const rotated = await refreshAccess(refresh);
    if (rotated) {
      currentAccess = rotated.access;
      rotatedRefresh = rotated.refresh;
      upstream = await djangoFetch(djangoPath, { method: request.method, headers, body }, currentAccess);
    }
  }

  const responseBody = upstream.status === 204 ? null : await upstream.arrayBuffer();
  const response = new NextResponse(responseBody, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
      "X-Request-ID": upstream.headers.get("x-request-id") ?? requestId,
    },
  });

  if (currentAccess && rotatedRefresh) setAuthCookies(response, currentAccess, rotatedRefresh);
  if (upstream.status === 401 && refresh && !rotatedRefresh) clearAuthCookies(response);
  return response;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
