import { NextResponse } from "next/server";
import { backendUrl, clearAuthCookies, currentTokens } from "@/lib/server-auth";

export async function POST() {
  const { refresh } = await currentTokens();
  if (refresh) {
    await fetch(backendUrl("auth/logout/"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    }).catch(() => null);
  }
  const response = new NextResponse(null, { status: 204 });
  clearAuthCookies(response);
  return response;
}
