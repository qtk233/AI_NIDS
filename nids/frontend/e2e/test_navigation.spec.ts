import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("navigates to big screen page", async ({ page }) => {
    await page.goto("/dashboard");
    await page.click("text=可视化大屏");
    await expect(page).toHaveURL(/\/bigscreen/);
    await expect(page.locator("h1")).toContainText("NIDS");
  });

  test("navigates to history page", async ({ page }) => {
    await page.goto("/dashboard");
    await page.click("text=历史记录");
    await expect(page).toHaveURL(/\/history/);
    await expect(page.locator("h1")).toContainText("历史记录");
  });

  test("navigates to model management page", async ({ page }) => {
    await page.goto("/dashboard");
    await page.click("text=模型管理");
    await expect(page).toHaveURL(/\/model/);
    await expect(page.locator("h1")).toContainText("模型管理");
  });

  test("navigates back to dashboard", async ({ page }) => {
    await page.goto("/history");
    await page.click("text=仪表盘");
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
