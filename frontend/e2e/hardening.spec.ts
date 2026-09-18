import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";
import { registerQaUser } from "./helpers";

test("social routes preserve authentication, query parameters and token refresh through BFF", async ({ page, context }) => {
  const user = await registerQaUser(page, "social117");
  const otherPage = await context.newPage();
  // Same browser registers the target, then signs back into the viewer account.
  const target = await registerQaUser(otherPage, "target117");
  await otherPage.close();
  const login = await page.request.post("/api/auth/login", { data: { nickname: user.nickname, password: user.password } });
  expect(login.ok()).toBeTruthy();
  const follow = await page.request.put(`/api/forum/users/${target.response.user.id}/follow/`);
  expect(follow.ok()).toBeTruthy();
  const list = await page.request.get(`/api/forum/social/users/${user.response.user.id}/following/?q=${target.nickname}&page_size=1`);
  expect(list.status()).toBe(200);
  expect((await list.json()).results.map((row: { user: { id: string } }) => row.user.id)).toEqual([target.response.user.id]);
  const empty = await page.request.get(`/api/forum/social/users/${user.response.user.id}/following/?q=no_such_account_117`);
  expect(empty.status()).toBe(200);
  expect((await empty.json()).results).toEqual([]);

  const access = (await context.cookies()).find((cookie) => cookie.name === "night_iris_access");
  expect(access).toBeDefined();
  await context.addCookies([{ ...access!, value: "expired-access-token" }]);
  const recommendations = await page.request.get("/api/forum/social/recommendations/?page_size=1", {
    headers: { "X-Request-ID": "hardening117-refresh" },
  });
  expect(recommendations.status()).toBe(200);
  expect(recommendations.headers()["x-request-id"]).toBe("hardening117-refresh");
  expect((await context.cookies()).find((cookie) => cookie.name === "night_iris_access")?.value).not.toBe("expired-access-token");
  const communities = await page.request.get("/api/forum/community-recommendations/?page_size=1");
  expect(communities.status()).toBe(200);
  expect(Array.isArray((await communities.json()).results)).toBeTruthy();
  await page.goto("/people");
  await expect(page.locator(".error-panel")).toHaveCount(0);
});

test("BFF retains authentication and route boundaries", async ({ request }) => {
  expect((await request.get("/api/forum/social/recommendations/")).status()).toBe(401);
  expect((await request.get("/api/forum/community-recommendations/")).status()).toBe(401);
  expect((await request.get("/api/forum/unexposed-internal-route/")).status()).toBe(404);
});

for (const [mode, endpoint] of [["Для вас", "/feed/for-you/"], ["Подписки", "/feed/"], ["Последние", "/publications/"]] as const) {
  test(`feed ${mode} loads subsequent pages through BFF and retains items on retry`, async ({ page }) => {
    await registerQaUser(page, "pages117");
    const created = await page.request.post("/api/forum/publications/", { data: {
      type: "post", title: "Pagination fixture", content: [{ type: "paragraph", text: "Pagination body" }], tags: [],
    } });
    expect(created.status()).toBe(201);
    const first = { ...await created.json(), title: "First page item" };
    const second = { ...first, id: randomUUID(), title: "Second page item" };
    let failNextPage = true;
    await page.route(`**/api/forum${endpoint}*`, async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname !== `/api/forum${endpoint}`) return route.continue();
      if (url.searchParams.has("cursor")) {
        expect(url.searchParams.get("cursor")).toBe("opaque+/=cursor");
        if (failNextPage) return route.fulfill({ status: 503, json: { detail: "Temporary outage" } });
        return route.fulfill({ json: { next: null, previous: null, results: [first, second] } });
      }
      return route.fulfill({ json: {
        next: `http://api:8000/api/v1${endpoint}?cursor=opaque%2B%2F%3Dcursor`, previous: null, results: [first],
      } });
    });
    await page.goto("/");
    await page.getByRole("tab", { name: mode, exact: true }).click();
    await expect(page.getByText(first.title, { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Показать ещё", exact: true }).click();
    await expect(page.getByRole("button", { name: "Повторить загрузку" })).toBeVisible();
    await expect(page.getByText(first.title, { exact: true })).toBeVisible();
    failNextPage = false;
    await page.getByRole("button", { name: "Повторить загрузку" }).click();
    await expect(page.getByText(second.title, { exact: true })).toBeVisible();
    await expect(page.locator(".feed-list .topic-card")).toHaveCount(2);
    await expect(page.getByRole("button", { name: "Показать ещё", exact: true })).toHaveCount(0);
  });
}

test("publish waits for in-flight autosave and persists the latest editor revision", async ({ page }) => {
  await registerQaUser(page, "save117");
  let releaseSave!: () => void;
  const gate = new Promise<void>((resolve) => { releaseSave = resolve; });
  let savedOnServer!: () => void;
  const saved = new Promise<void>((resolve) => { savedOnServer = resolve; });
  let creates = 0;
  await page.route("**/api/forum/publication-drafts/", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    creates += 1;
    const response = await route.fetch();
    savedOnServer();
    await gate;
    await route.fulfill({ response });
  });
  await page.goto("/new");
  await page.getByPlaceholder("Сформулируйте вопрос").fill("Earlier revision");
  await page.getByPlaceholder("Текст абзаца…").fill("Earlier body");
  await saved;
  await page.getByPlaceholder("Сформулируйте вопрос").fill("Latest revision 117");
  await page.getByPlaceholder("Текст абзаца…").fill("Latest body 117");
  const published = page.waitForResponse((response) => /\/publish\/?$/.test(response.url()) && response.request().method() === "POST" && response.status() !== 308);
  await page.getByRole("button", { name: "Опубликовать", exact: true }).click();
  await expect(page.getByPlaceholder("Сформулируйте вопрос")).toBeDisabled();
  releaseSave();
  const response = await published;
  expect(response.status()).toBe(201);
  const publication = await response.json();
  expect(publication.title).toBe("Latest revision 117");
  expect(publication.content).toEqual([{ type: "paragraph", text: "Latest body 117" }]);
  expect(creates).toBe(1);
  await expect(page).toHaveURL(new RegExp(`/publications/${publication.id}$`));
  const drafts = await page.request.get("/api/forum/publication-drafts/");
  expect((await drafts.json()).results).toEqual([]);
});

test("failed final save keeps editor content and does not publish stale data", async ({ page }) => {
  await registerQaUser(page, "failed117");
  let rejectSave = true;
  let publications = 0;
  page.on("request", (request) => {
    if (request.url().includes("/publish/") && request.method() === "POST") publications += 1;
  });
  await page.route("**/api/forum/publication-drafts/", async (route) => {
    if (route.request().method() === "POST" && rejectSave) {
      return route.fulfill({ status: 503, json: { detail: "Save temporarily unavailable" } });
    }
    return route.continue();
  });
  await page.goto("/new");
  await page.getByPlaceholder("Сформулируйте вопрос").fill("Retryable publication");
  await page.getByPlaceholder("Текст абзаца…").fill("Preserved content");
  await page.getByRole("button", { name: "Опубликовать", exact: true }).click();
  await expect(page.locator(".form-error")).toContainText("Save temporarily unavailable");
  expect(publications).toBe(0);
  await expect(page.getByPlaceholder("Текст абзаца…")).toHaveValue("Preserved content");
  rejectSave = false;
  await page.getByRole("button", { name: "Опубликовать", exact: true }).click();
  await expect(page).toHaveURL(/\/publications\/[0-9a-f-]+$/);
  expect(publications).toBe(1);
});
