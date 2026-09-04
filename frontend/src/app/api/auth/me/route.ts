
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

export async function GET(request: Request) {
  const requestId = requestIdFor(request);
  const { access, refresh } = await currentTokens();

  if (!access && !refresh) {
    return NextResponse.json(
      { user: null },
      {
        headers: {
          "X-Request-ID": requestId,
        },
      },
    );
  }

  try {
    let currentAccess = access;
    let rotatedRefresh: string | undefined;
    let upstream = currentAccess
      ? await djangoFetch(
          "users/me/",
          {},
          currentAccess,
          requestId,
        )
      : null;

    if (
      (!upstream || upstream.status === 401) &&
      refresh
    ) {
      const rotated = await refreshAccess(
        refresh,
        requestId,
      );

      if (rotated) {
        currentAccess = rotated.access;
        rotatedRefresh = rotated.refresh;
        upstream = await djangoFetch(
          "users/me/",
          {},
          currentAccess,
          requestId,
        );
      }
    }

    if (!upstream || upstream.status === 401) {
      const response = NextResponse.json(
        { user: null },
        {
          headers: {
            "X-Request-ID": requestId,
          },
        },
      );
      clearAuthCookies(response);
      return response;
    }

    const responseRequestId =
      upstream.headers.get("x-request-id") ?? requestId;

    if (!upstream.ok) {
      const payload = await upstream
        .json()
        .catch(() => null);
      return NextResponse.json(
        payload ?? {
          error: {
            code: "upstream_error",
            message: "Backend request failed.",
            status: upstream.status,
            request_id: responseRequestId,
          },
        },
        {
          status: upstream.status,
          headers: {
            "X-Request-ID": responseRequestId,
          },
        },
      );
    }

    const user = await upstream.json();
    const response = NextResponse.json(
      { user },
      {
        headers: {
          "X-Request-ID": responseRequestId,
        },
      },
    );

    if (currentAccess && rotatedRefresh) {
      setAuthCookies(
        response,
        currentAccess,
        rotatedRefresh,
      );
    }

    return response;
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return backendUnavailableResponse(error, requestId);
    }
    throw error;
  }
}
