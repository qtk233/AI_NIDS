import { test, expect } from "@playwright/test";

test.describe("Dashboard Page", () => {
  test("loads and shows title", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.locator("h1")).toContainText("仪表盘");
  });

  test("shows navigation sidebar", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.locator("text=实时检测")).toBeVisible();
    await expect(page.locator("text=可视化大屏")).toBeVisible();
    await expect(page.locator("text=历史记录")).toBeVisible();
    await expect(page.locator("text=模型管理")).toBeVisible();
  });

  test("displays stat cards", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.locator("text=检测总数")).toBeVisible();
    await expect(page.locator("text=告警数")).toBeVisible();
    await expect(page.locator("text=准确率")).toBeVisible();
  });

  test("redirects root to dashboard", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
