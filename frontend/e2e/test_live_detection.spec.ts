import { test, expect } from "@playwright/test";

test.describe("Live Detection Page", () => {
  test("loads and shows title", async ({ page }) => {
    await page.goto("/live");
    await expect(page.locator("h1")).toContainText("实时检测");
  });

  test("shows connection status", async ({ page }) => {
    await page.goto("/live");
    await expect(page.locator("text=重连中...")).toBeVisible();
  });

  test("shows empty table placeholder", async ({ page }) => {
    await page.goto("/live");
    await expect(page.locator("text=暂无检测数据")).toBeVisible();
  });

  test("has clear button", async ({ page }) => {
    await page.goto("/live");
    await expect(page.getByText("清空")).toBeVisible();
  });
});
