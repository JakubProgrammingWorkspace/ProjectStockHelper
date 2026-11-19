import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/StockHelper/i);
});

test('loads tickers list', async ({ page }) => {
  await page.goto('/');
  // Wait for the select to be populated
  const tickerSelect = page.locator('#ticker');
  await expect(tickerSelect).toBeVisible();
});
