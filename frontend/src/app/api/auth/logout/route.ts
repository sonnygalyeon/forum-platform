
import { NextResponse } from "next/server";
import {
  backendFetch,
  clearAuthCookies,
  currentTokens,
  requestIdFor,
} from "@/lib/server-auth";

export async function POST(request: Request) {
  const requestId = requestIdFor(request);
  const { refresh } = await currentTokens();

  if (refresh) {
    await backendFetch(
      "auth/logout/",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh }),
      },
      { requestId },
    ).catch(() => null);
  }

  const response = new NextResponse(null, {
    status: 204,
    headers: {
      "X-Request-ID": requestId,
    },
  });
  clearAuthCookies(response);
  return response;
}
