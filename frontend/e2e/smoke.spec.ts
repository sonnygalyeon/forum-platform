import { expect, test } from "@playwright/test";
import {
  expectBrowserAuthenticated,
  registerQaUser,
} from "./helpers";

test("auth cookie survives navigation and main shell renders", async ({
  page,
}) => {
  const user = await registerQaUser(
    page,
    "smoke",
  );

  await page.goto("/");

  await expectBrowserAuthenticated(
    page,
    user.nickname,
  );

  await expect(
    page
      .getByRole("link", {
        name: "Профиль",
      })
      .first(),
  ).toBeVisible({
    timeout: 10_000,
  });

  await expect(
    page
      .getByRole("link", {
        name: "Сообщения",
      })
      .first(),
  ).toBeVisible();

  await page.goto("/messages");

  await expect(page).toHaveURL(
    /\/messages/,
  );

  await expect(
    page.locator("body"),
  ).toContainText(
    /Сообщения|Messenger|Мессенджер/i,
  );
});

test("article can be created through the frontend BFF and opened", async ({
  page,
}) => {
  await registerQaUser(
    page,
    "article",
  );

  const title =
    `Playwright article ${Date.now()}`;

  const createResult =
    await page.evaluate(
      async ({ title }) => {
        const response = await fetch(
          "/api/forum/publications",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            credentials: "same-origin",
            body: JSON.stringify({
              type: "article",
              title,
              content: [
                {
                  type: "paragraph",
                  text:
                    "Created by the Stage 8.11 browser smoke test.",
                },
              ],
              tags: [
                "playwright",
                "e2e",
              ],
            }),
          },
        );

        return {
          status: response.status,
          body: await response.json(),
        };
      },
      { title },
    );

  expect(createResult.status).toBe(201);

  await page.goto(
    `/publications/${createResult.body.id}`,
  );

  await expect(
    page.getByText(
      title,
      {
        exact: true,
      },
    ),
  ).toBeVisible();
});

test("mobile messenger does not overflow horizontally", async ({
  page,
}) => {
  await page.setViewportSize({
    width: 390,
    height: 844,
  });

  await registerQaUser(
    page,
    "mobile",
  );

  await page.goto("/messages");

  const overflow =
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    );

  expect(overflow).toBeLessThanOrEqual(1);
});
