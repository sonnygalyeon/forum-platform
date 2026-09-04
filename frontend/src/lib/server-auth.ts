
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const backendBase = (
  process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

const configuredTimeout = Number(
  process.env.BACKEND_FETCH_TIMEOUT_MS ?? "10000",
);
const backendTimeoutMs =
  Number.isFinite(configuredTimeout) && configuredTimeout > 0
    ? configuredTimeout
    : 10_000;

const disableKeepAlive =
  process.env.BACKEND_DISABLE_KEEPALIVE === "1";

const SAFE_RETRY_METHODS = new Set([
  "GET",
  "HEAD",
  "OPTIONS",
]);

export const ACCESS_COOKIE = "night_iris_access";
export const REFRESH_COOKIE = "night_iris_refresh";

const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

export class BackendUnavailableError extends Error {
  constructor(
    message: string,
    public readonly requestId: string,
    public readonly causeValue?: unknown,
  ) {
    super(message);
    this.name = "BackendUnavailableError";
  }
}

export function backendUrl(path: string) {
  return `${backendBase}/${path.replace(/^\//, "")}`;
}

export function requestIdFor(request: Request) {
  return (
    request.headers.get("x-request-id") ??
    crypto.randomUUID()
  );
}

export function setAuthCookies(
  response: NextResponse,
  access: string,
  refresh?: string,
) {
  response.cookies.set(ACCESS_COOKIE, access, {
    ...cookieOptions,
    maxAge: 60 * 15,
  });

  if (refresh) {
    response.cookies.set(REFRESH_COOKIE, refresh, {
      ...cookieOptions,
      maxAge: 60 * 60 * 24 * 30,
    });
  }
}

export function clearAuthCookies(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", {
    ...cookieOptions,
    maxAge: 0,
  });
  response.cookies.set(REFRESH_COOKIE, "", {
    ...cookieOptions,
    maxAge: 0,
  });
}

export async function currentTokens() {
  const store = await cookies();
  return {
    access: store.get(ACCESS_COOKIE)?.value ?? null,
    refresh: store.get(REFRESH_COOKIE)?.value ?? null,
  };
}

function delay(ms: number) {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, ms);
  });
}

function describeError(error: unknown) {
  if (error instanceof Error) {
    const cause = error.cause;
    if (cause && typeof cause === "object") {
      const code = (cause as { code?: unknown }).code;
      if (typeof code === "string") {
        return `${error.name}:${code}`;
      }
    }
    return error.name;
  }
  return "unknown";
}

export async function backendFetch(
  path: string,
  init: RequestInit = {},
  options: {
    access?: string | null;
    requestId?: string;
  } = {},
) {
  const method = (init.method ?? "GET").toUpperCase();
  const requestId = options.requestId ?? crypto.randomUUID();
  const maxAttempts = SAFE_RETRY_METHODS.has(method) ? 2 : 1;

  const headers = new Headers(init.headers);
  headers.set("X-Request-ID", requestId);

  if (options.access) {
    headers.set(
      "Authorization",
      `Bearer ${options.access}`,
    );
  }

  // Useful for macOS/Docker Desktop development where stale keep-alive
  // sockets can produce ECONNRESET in Node/Undici. Production keeps pooling.
  if (disableKeepAlive) {
    headers.set("Connection", "close");
  }

  let lastError: unknown = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(
      () => controller.abort(),
      backendTimeoutMs,
    );

    const sourceSignal = init.signal;
    const abortFromSource = () =>
      controller.abort(sourceSignal?.reason);

    if (sourceSignal) {
      if (sourceSignal.aborted) {
        abortFromSource();
      } else {
        sourceSignal.addEventListener(
          "abort",
          abortFromSource,
          { once: true },
        );
      }
    }

    try {
      return await fetch(backendUrl(path), {
        ...init,
        headers,
        cache: "no-store",
        signal: controller.signal,
      });
    } catch (error) {
      lastError = error;
      if (attempt < maxAttempts) {
        await delay(100 * attempt);
        continue;
      }
    } finally {
      clearTimeout(timeout);
      sourceSignal?.removeEventListener(
        "abort",
        abortFromSource,
      );
    }
  }

  console.error("[night-iris:bff] upstream unavailable", {
    requestId,
    method,
    path,
    timeoutMs: backendTimeoutMs,
    error: describeError(lastError),
  });

  throw new BackendUnavailableError(
    "Night Iris backend is temporarily unavailable.",
    requestId,
    lastError,
  );
}

export function backendUnavailableResponse(
  error: unknown,
  fallbackRequestId?: string,
) {
  const requestId =
    error instanceof BackendUnavailableError
      ? error.requestId
      : fallbackRequestId ?? crypto.randomUUID();

  return NextResponse.json(
    {
      error: {
        code: "upstream_unavailable",
        message:
          "Backend service is temporarily unavailable.",
        status: 502,
        request_id: requestId,
      },
    },
    {
      status: 502,
      headers: {
        "X-Request-ID": requestId,
      },
    },
  );
}

export async function refreshAccess(
  refresh: string,
  requestId?: string,
) {
  const response = await backendFetch(
    "auth/refresh/",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh }),
    },
    { requestId },
  );

  if (!response.ok) return null;

  const data = (await response.json()) as {
    access?: string;
    refresh?: string;
  };

  if (!data.access) return null;

  return {
    access: data.access,
    refresh: data.refresh ?? refresh,
  };
}

export async function djangoFetch(
  path: string,
  init: RequestInit = {},
  access?: string | null,
  requestId?: string,
) {
  return backendFetch(path, init, {
    access,
    requestId,
  });
}
