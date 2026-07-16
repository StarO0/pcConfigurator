import { expect, test } from "@playwright/test";

test("opens builder and full catalog on desktop and mobile", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/PC/i);
  await page.getByTestId("nav-catalog").click();
  await expect(page.getByTestId("catalog-page")).toBeVisible();
  await expect(page.getByText(/товаров/i).first()).toBeVisible();
  await page.getByTestId("nav-builder").click();
  await expect(page.getByTestId("nav-builder")).toHaveClass(/text-cyan/);
});

test("data workspace presents local admin access", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("nav-data").click();
  await expect(page.getByText("Локальная панель данных")).toBeVisible();
  await expect(page.getByText("admin@pcbuilder.app")).toBeVisible();
});
