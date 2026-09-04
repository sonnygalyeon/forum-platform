import { expect, test } from "@playwright/test";
import { expectBrowserAuthenticated, registerQaUser } from "./helpers";

test("auth cookie survives navigation and 0.9 shell renders", async ({ page }) => {
  const user = await registerQaUser(page, "smoke");
  await page.goto("/");
  await expectBrowserAuthenticated(page, user.nickname);
  await expect(page.getByRole("link", { name: "Профиль" }).first()).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole("link", { name: "Сообщения" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Открыть" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Сохранённое" }).first()).toBeVisible();

  await page.goto("/messages");
  await expect(page).toHaveURL(/\/messages/);
  await expect(page.locator("body")).toContainText(/Сообщения|Messenger|Мессенджер/i);
});

test("article can be created through the frontend BFF and opened", async ({ page }) => {
  await registerQaUser(page, "article");
  const title = `Playwright article ${Date.now()}`;
  const createResult = await page.evaluate(async ({ title }) => {
    const response = await fetch("/api/forum/publications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({
        type: "article",
        title,
        content: [{ type: "paragraph", text: "Created by the 0.9 browser smoke test." }],
        tags: ["playwright", "e2e"],
      }),
    });
    return { status: response.status, body: await response.json() };
  }, { title });
  expect(createResult.status).toBe(201);
  await page.goto(`/publications/${createResult.body.id}`);
  await expect(page.getByText(title, { exact: true })).toBeVisible();
});

test("0.9 server draft can be saved and published through the BFF", async ({ page }) => {
  await registerQaUser(page, "draft-beta");
  const result = await page.evaluate(async () => {
    const headers = { "Content-Type": "application/json" };
    const created = await fetch("/api/forum/publication-drafts", {
      method: "POST",
      headers,
      credentials: "same-origin",
      body: JSON.stringify({ type: "article", title: "", content: [], tags: [] }),
    });
    const draft = await created.json();
    const saved = await fetch(`/api/forum/publication-drafts/${draft.id}`, {
      method: "PATCH",
      headers,
      credentials: "same-origin",
      body: JSON.stringify({
        title: "0.9 autosave smoke",
        content: [
          { type: "paragraph", text: "Durable server draft" },
          { type: "embed", url: "https://example.com/reference", title: "Reference" },
        ],
        tags: ["draft", "beta"],
      }),
    });
    const savedBody = await saved.json();
    const published = await fetch(`/api/forum/publication-drafts/${draft.id}/publish`, {
      method: "POST",
      credentials: "same-origin",
    });
    const publication = await published.json();
    return { created: created.status, saved: saved.status, savedBody, published: published.status, publication };
  });
  expect(result.created).toBe(201);
  expect(result.saved).toBe(200);
  expect(result.savedBody.title).toBe("0.9 autosave smoke");
  expect(result.published).toBe(201);
  await page.goto(`/publications/${result.publication.id}`);
  await expect(page.getByText("0.9 autosave smoke", { exact: true })).toBeVisible();
});

test("0.9 product surfaces are reachable for an authenticated user", async ({ page }) => {
  await registerQaUser(page, "surfaces");
  const surfaces = [
    ["/discover", /Найти полезное/i],
    ["/saved", /Сохранённые публикации/i],
    ["/drafts", /Незавершённые публикации/i],
    ["/reports", /Мои обращения/i],
    ["/profile/progress", /Как растёт ваша репутация/i],
  ] as const;
  for (const [path, text] of surfaces) {
    await page.goto(path);
    await expect(page.locator("body")).toContainText(text, { timeout: 10_000 });
  }
});

test("mobile messenger does not overflow horizontally", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await registerQaUser(page, "mobile");
  await page.goto("/messages");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});
