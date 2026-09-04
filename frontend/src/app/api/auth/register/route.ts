
import { NextResponse } from "next/server";
import {
  BackendUnavailableError,
  backendFetch,
  backendUnavailableResponse,
  requestIdFor,
  setAuthCookies,
} from "@/lib/server-auth";

type AuthResponse = {
  user?: unknown;
  access?: string;
  refresh?: string;
};

export async function POST(request: Request) {
  const requestId = requestIdFor(request);

  try {
    const body = await request.text();
    const upstream = await backendFetch(
      "auth/register/",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body,
      },
      { requestId },
    );

    const data = (await upstream
      .json()
      .catch(() => null)) as AuthResponse | null;

    const responseRequestId =
      upstream.headers.get("x-request-id") ?? requestId;

    if (!upstream.ok) {
      return NextResponse.json(
        data ?? { detail: "Registration failed" },
        {
          status: upstream.status,
          headers: {
            "X-Request-ID": responseRequestId,
          },
        },
      );
    }

    if (
      !data?.user ||
      typeof data.access !== "string" ||
      typeof data.refresh !== "string"
    ) {
      return NextResponse.json(
        {
          error: {
            code: "invalid_upstream_response",
            message:
              "Backend returned an invalid authentication response.",
            status: 502,
            request_id: responseRequestId,
          },
        },
        {
          status: 502,
          headers: {
            "X-Request-ID": responseRequestId,
          },
        },
      );
    }

    const response = NextResponse.json(
      { user: data.user },
      {
        status: 201,
        headers: {
          "X-Request-ID": responseRequestId,
        },
      },
    );

    setAuthCookies(
      response,
      data.access,
      data.refresh,
    );

    return response;
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return backendUnavailableResponse(error, requestId);
    }
    throw error;
  }
}
