export class ApiError extends Error {
  constructor(
    public status: number,
    public payload: unknown,
    message = "API request failed",
  ) {
    super(message);
  }
}

export async function clientApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/forum${path}`, {
    ...init,
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(init.headers ?? {}),
    },
  });

  const payload = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, payload);
  }
  return payload as T;
}

export function errorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return "Не удалось выполнить запрос.";
  const payload = error.payload;
  if (payload && typeof payload === "object") {
    const data = payload as Record<string, unknown>;
    if (data.error && typeof data.error === "object") {
      const apiError = data.error as Record<string, unknown>;
      const fields = apiError.fields;
      if (fields && typeof fields === "object") {
        for (const value of Object.values(fields as Record<string, unknown>)) {
          if (Array.isArray(value) && typeof value[0] === "string") return value[0];
          if (typeof value === "string") return value;
        }
      }
      if (typeof apiError.message === "string") return apiError.message;
    }
    if (typeof data.detail === "string") return data.detail;
    for (const value of Object.values(data)) {
      if (Array.isArray(value) && typeof value[0] === "string") return value[0];
      if (typeof value === "string") return value;
    }
  }
  return `Ошибка API (${error.status}).`;
}
