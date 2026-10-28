import { test, expect } from '@playwright/test'

test('complete dashboard workflows and responsive navigation', async ({ page }) => {
  const browserErrors: string[] = []
  page.on('pageerror', (error) => browserErrors.push(error.message))
  await page.goto('/settings')
  await expect(page.getByRole('heading', { name: 'Data & settings' })).toBeVisible()
  const demo = page.getByRole('button', { name: 'Load demo dataset' })
  await expect(page.getByText('Customers', { exact: true })).toBeVisible()
  const status = await page.request.get('/api/v1/data/status')
  if ((await status.json()).demo_available) {
    await expect(demo).toBeEnabled()
    await demo.click()
    await expect(
      page.getByRole('status').filter({ hasText: 'Synthetic demonstration dataset loaded' }),
    ).toBeVisible({ timeout: 60000 })
  }
  await page.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Category performance' })).toBeVisible()
  await expect(page.locator('main table tbody tr')).toHaveCount(8)
  await page.screenshot({
    path: 'test-results/overview-desktop.png',
    fullPage: true,
    animations: 'disabled',
  })

  await page.getByRole('link', { name: 'Forecast', exact: true }).click()
  await page.getByLabel('Model', { exact: true }).selectOption('ma')
  await expect(page.getByRole('heading', { name: 'Model validation' })).toBeVisible({
    timeout: 60000,
  })
  await page.getByLabel('Forecast horizon').selectOption('7')
  await expect(page.getByText('7-day predicted demand', { exact: true })).toBeVisible()
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download CSV' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('forecast.csv')
  await page.getByLabel('Forecast level').selectOption('category')
  await expect(page.getByRole('heading', { name: 'Model validation' })).toBeVisible({
    timeout: 60000,
  })
  await page.screenshot({
    path: 'test-results/forecast-desktop.png',
    fullPage: true,
    animations: 'disabled',
  })

  await page.getByRole('link', { name: 'Customer', exact: true }).click()
  await page.getByLabel('Search by name, email, or customer ID').fill('CUST_000001')
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  await page.getByRole('button').filter({ hasText: 'CUST_000001' }).click()
  await expect(page.getByRole('heading', { name: 'Recommended products' })).toBeVisible({
    timeout: 60000,
  })
  await page.getByText('Explain prediction', { exact: true }).first().click()
  await expect(page.getByRole('heading', { name: 'Recent activity' })).toBeVisible()
  await page.screenshot({
    path: 'test-results/customer-desktop.png',
    fullPage: true,
    animations: 'disabled',
  })

  await page.getByRole('link', { name: 'Segments', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Segment distribution' })).toBeVisible()
  await page.getByRole('button', { name: 'View customers' }).first().click()
  await expect(page.locator('main table tbody tr').first()).toBeVisible()

  await page.getByRole('link', { name: 'Insights', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Product inventory plan' })).toBeVisible()
  await page.getByLabel('Planning horizon').selectOption('7')
  await page.getByLabel('Show products').selectOption('stockout')
  await expect(page.getByText('Within 7 days', { exact: true })).toBeVisible()

  await page.getByRole('link', { name: 'Settings', exact: true }).click()
  await page.getByLabel('Products CSV', { exact: true }).setInputFiles({
    name: 'bad.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('bad_column\ninvalid'),
  })
  await page.getByRole('button', { name: 'Validate and import' }).click()
  await expect(page.getByRole('alert')).toContainText('Missing columns')

  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'Open navigation' }).click()
  await page.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Open navigation' }).click()
  await page.getByRole('button', { name: 'Switch to dark theme' }).click()
  await page.getByRole('button', { name: 'Close sidebar' }).click()
  await expect(page.locator('html')).toHaveClass(/dark/)
  await expect(page.getByRole('link', { name: 'Overview', exact: true })).not.toBeVisible()
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1),
  ).toBeTruthy()
  await page.screenshot({
    path: 'test-results/overview-mobile-dark.png',
    fullPage: true,
    animations: 'disabled',
  })
  expect(browserErrors).toEqual([])
})
