import { NextResponse } from "next/server";
import { clearAuthCookies, currentTokens, djangoFetch, refreshAccess, setAuthCookies } from "@/lib/server-auth";

export async function GET() {
  const { access, refresh } = await currentTokens();
  if (!access && !refresh) return NextResponse.json({ user: null });

  let currentAccess = access;
  let rotatedRefresh: string | undefined;
  let upstream = currentAccess ? await djangoFetch("users/me/", {}, currentAccess) : null;

  if ((!upstream || upstream.status === 401) && refresh) {
    const rotated = await refreshAccess(refresh);
    if (rotated) {
      currentAccess = rotated.access;
      rotatedRefresh = rotated.refresh;
      upstream = await djangoFetch("users/me/", {}, currentAccess);
    }
  }

  if (!upstream || !upstream.ok) {
    const response = NextResponse.json({ user: null });
    clearAuthCookies(response);
    return response;
  }

  const user = await upstream.json();
  const response = NextResponse.json({ user });
  if (currentAccess && rotatedRefresh) setAuthCookies(response, currentAccess, rotatedRefresh);
  return response;
}
