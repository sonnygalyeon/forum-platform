
import { NextResponse } from "next/server";
import {
  BackendUnavailableError,
  backendUnavailableResponse,
  clearAuthCookies,
  currentTokens,
  djangoFetch,
  refreshAccess,
  requestIdFor,
  setAuthCookies,
} from "@/lib/server-auth";

const ALLOWED_ROOTS = new Set([
  "publications",
  "publication-drafts",
  "feed",
  "communities",
  "notifications",
  "users",
  "comments",
  "admin",
  "moderation",
  "ready",
  "uploads",
  "identity",
  "search",
  "discover",
  "messenger",
  "observability",
]);

type Context = {
  params: Promise<{ path: string[] }>;
};

async function proxy(
  request: Request,
  context: Context,
) {
  const requestId = requestIdFor(request);
  const { path } = await context.params;

  if (!path.length || !ALLOWED_ROOTS.has(path[0])) {
    return NextResponse.json(
      { detail: "Endpoint is not exposed by the frontend proxy." },
      { status: 404, headers: { "X-Request-ID": requestId } },
    );
  }

  try {
    const incomingUrl = new URL(request.url);
    const djangoPath = `${path.join("/")}/${incomingUrl.search}`;
    const body = ["GET", "HEAD"].includes(request.method)
      ? undefined
      : await request.arrayBuffer();

    const headers = new Headers();
    const contentType = request.headers.get("content-type");
    if (contentType) headers.set("Content-Type", contentType);

    const { access, refresh } = await currentTokens();
    let currentAccess = access;
    let rotatedRefresh: string | undefined;

    let upstream = await djangoFetch(
      djangoPath,
      { method: request.method, headers, body },
      currentAccess,
      requestId,
    );

    if (upstream.status === 401 && refresh) {
      const rotated = await refreshAccess(refresh, requestId);
      if (rotated) {
        currentAccess = rotated.access;
        rotatedRefresh = rotated.refresh;
        upstream = await djangoFetch(
          djangoPath,
          { method: request.method, headers, body },
          currentAccess,
          requestId,
        );
      }
    }

    const responseBody = upstream.status === 204 ? null : await upstream.arrayBuffer();
    const responseRequestId = upstream.headers.get("x-request-id") ?? requestId;
    const response = new NextResponse(responseBody, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") ?? "application/json",
        "X-Request-ID": responseRequestId,
      },
    });

    if (currentAccess && rotatedRefresh) {
      setAuthCookies(response, currentAccess, rotatedRefresh);
    }
    if (upstream.status === 401 && refresh && !rotatedRefresh) {
      clearAuthCookies(response);
    }
    return response;
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return backendUnavailableResponse(error, requestId);
    }
    throw error;
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
