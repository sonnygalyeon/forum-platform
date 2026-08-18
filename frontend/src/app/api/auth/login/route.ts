import { NextResponse } from "next/server";
import { backendUrl, setAuthCookies } from "@/lib/server-auth";

export async function POST(request: Request) {
  const body = await request.text();
  const upstream = await fetch(backendUrl("auth/login/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    cache: "no-store",
  });
  const data = await upstream.json().catch(() => null);
  if (!upstream.ok) return NextResponse.json(data ?? { detail: "Login failed" }, { status: upstream.status });
  const response = NextResponse.json({ user: data.user });
  setAuthCookies(response, data.access, data.refresh);
  return response;
}
