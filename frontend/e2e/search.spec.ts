import { expect, test, type Page } from "@playwright/test";
import { registerQaUser } from "./helpers";

async function seedSearch(page: Page) {
  await registerQaUser(page, "search120");
  const needle = `needle${Date.now()}${Math.random().toString(16).slice(2, 8)}`;
  for (let i = 0; i < 7; i++) {
    const response = await page.request.post("/api/forum/publications/", { data: {
      type: i === 0 ? "post" : "article", title: `${needle} result ${i}`,
      content: [{ type: "paragraph", text: "Search navigation content" }], tags: [needle],
    } });
    expect(response.status()).toBe(201);
  }
  return needle;
}

test("search opens full results and preserves filters, reload and browser history", async ({ page }) => {
  const needle = await seedSearch(page);
  await page.goto(`/search?q=${needle}&sort=latest&date=week&page_size=2`);
  await expect(page.locator(".search-results-stack .topic-card")).toHaveCount(6);
  await page.getByRole("button", { name: "Все результаты: публикации", exact: true }).click();
  await expect(page.locator(".search-results-stack .topic-card")).toHaveCount(2);
  await expect(page.getByText("Страница 1 из 4", { exact: true })).toBeVisible();
  const titles = await page.locator(".search-results-stack .topic-title").allTextContents();
  await page.getByRole("button", { name: "Следующая", exact: true }).click();
  await expect(page.getByText("Страница 2 из 4", { exact: true })).toBeVisible();
  expect(await page.locator(".search-results-stack .topic-title").allTextContents()).not.toEqual(titles);
  const url = new URL(page.url());
  expect(url.searchParams.get("q")).toBe(needle);
  expect(url.searchParams.get("sort")).toBe("latest");
  expect(url.searchParams.get("date")).toBe("week");
  expect(url.searchParams.get("page")).toBe("2");
  await page.reload();
  await expect(page.getByText("Страница 2 из 4", { exact: true })).toBeVisible();
  await page.goBack();
  await expect(page.getByText("Страница 1 из 4", { exact: true })).toBeVisible();
  await page.goForward();
  await expect(page.getByText("Страница 2 из 4", { exact: true })).toBeVisible();
  await page.getByLabel("Тип", { exact: true }).selectOption("article");
  await expect(page.getByText("Страница 1 из 3", { exact: true })).toBeVisible();
  expect(new URL(page.url()).searchParams.has("page")).toBe(false);
  await page.getByRole("button", { name: "Следующая", exact: true }).click();
  await expect(page.getByText("Страница 2 из 3", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: /Люди/ }).click();
  await expect(page).toHaveURL(/scope=users/);
  expect(new URL(page.url()).searchParams.has("page")).toBe(false);
  await expect(page.getByText("Пользователей не найдено.", { exact: true })).toBeVisible();
});

test("search supports anonymous browsing without text and recovery from an invalid page", async ({ page }) => {
  const needle = await seedSearch(page);
  await page.request.post("/api/auth/logout");
  await page.goto("/search?scope=publications&type=article&page_size=2");
  await expect(page.locator(".search-results-stack .topic-card")).toHaveCount(2);
  await expect(page.getByRole("tab", { name: /Публикации/ })).toHaveAttribute("aria-selected", "true");
  await page.goto(`/search?q=${needle}&scope=publications&page_size=2&page=999999`);
  await expect(page.getByRole("alert")).toBeVisible();
  await page.getByRole("button", { name: "На первую страницу", exact: true }).click();
  await expect(page.getByText("Страница 1 из 4", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Следующая", exact: true }).click();
  await expect(page.getByText("Страница 2 из 4", { exact: true })).toBeVisible();
  await page.getByRole("textbox", { name: "Поисковый запрос" }).fill(`${needle} missingterm`);
  await page.getByRole("button", { name: "Найти", exact: true }).click();
  await expect(page.getByText("Публикаций не найдено.", { exact: true })).toBeVisible();
  expect(new URL(page.url()).searchParams.has("page")).toBe(false);
});
