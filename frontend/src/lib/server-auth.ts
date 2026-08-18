import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const backendBase = (process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");
export const ACCESS_COOKIE = "night_iris_access";
export const REFRESH_COOKIE = "night_iris_refresh";

const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

export function backendUrl(path: string) {
  return `${backendBase}/${path.replace(/^\//, "")}`;
}

export function setAuthCookies(response: NextResponse, access: string, refresh?: string) {
  response.cookies.set(ACCESS_COOKIE, access, { ...cookieOptions, maxAge: 60 * 15 });
  if (refresh) {
    response.cookies.set(REFRESH_COOKIE, refresh, { ...cookieOptions, maxAge: 60 * 60 * 24 * 30 });
  }
}

export function clearAuthCookies(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", { ...cookieOptions, maxAge: 0 });
  response.cookies.set(REFRESH_COOKIE, "", { ...cookieOptions, maxAge: 0 });
}

export async function currentTokens() {
  const store = await cookies();
  return {
    access: store.get(ACCESS_COOKIE)?.value ?? null,
    refresh: store.get(REFRESH_COOKIE)?.value ?? null,
  };
}

export async function refreshAccess(refresh: string) {
  const response = await fetch(backendUrl("auth/refresh/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });
  if (!response.ok) return null;
  const data = (await response.json()) as { access?: string; refresh?: string };
  if (!data.access) return null;
  return { access: data.access, refresh: data.refresh ?? refresh };
}

export async function djangoFetch(path: string, init: RequestInit = {}, access?: string | null) {
  const headers = new Headers(init.headers);
  if (access) headers.set("Authorization", `Bearer ${access}`);
  return fetch(backendUrl(path), { ...init, headers, cache: "no-store" });
}
