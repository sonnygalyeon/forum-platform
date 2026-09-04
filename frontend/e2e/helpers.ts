import {
  expect,
  type Page,
} from "@playwright/test";

type RegisterPayload = {
  nickname: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  country: string;
  nationality: string;
  interface_language: string;
};

type RegisterResponse = {
  user: {
    id: string;
    nickname: string;
  };
};

export type RegisterResult = RegisterPayload & {
  response: RegisterResponse;
};

export async function browserMe(page: Page) {
  return page.evaluate(async () => {
    const response = await fetch("/api/auth/me", {
      cache: "no-store",
      credentials: "same-origin",
    });

    const body = await response.json();

    return {
      status: response.status,
      body,
    };
  });
}

export async function expectBrowserAuthenticated(
  page: Page,
  nickname: string,
) {
  await expect
    .poll(
      async () => {
        const result = await browserMe(page);

        if (result.status !== 200) {
          return `status:${result.status}`;
        }

        return result.body?.user?.nickname ?? null;
      },
      {
        message:
          "The actual browser must be authenticated through /api/auth/me",
        timeout: 10_000,
      },
    )
    .toBe(nickname);
}

export async function registerQaUser(
  page: Page,
  prefix = "e2e",
): Promise<RegisterResult> {
  const suffix =
    `${Date.now()}_` +
    Math.random().toString(16).slice(2, 8);

  const nickname =
    `${prefix}_${suffix}`.slice(0, 31);

  const payload: RegisterPayload = {
    nickname,
    email: `${nickname}@example.test`,
    password: "StrongE2EPass_2026!",
    first_name: "E2E",
    last_name: "Tester",
    country: "DE",
    nationality: "DE",
    interface_language: "ru",
  };

  await page.goto("/");

  const result = await page.evaluate(
    async (body) => {
      const response = await fetch(
        "/api/auth/register",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "same-origin",
          body: JSON.stringify(body),
        },
      );

      let data: unknown = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      return {
        status: response.status,
        data,
      };
    },
    payload,
  );

  expect(
    result.status,
    `Registration failed: ${JSON.stringify(result.data)}`,
  ).toBe(201);

  const body = result.data as RegisterResponse;

  expect(body.user.nickname).toBe(nickname);

  await expectBrowserAuthenticated(
    page,
    nickname,
  );

  return {
    ...payload,
    response: body,
  };
}
