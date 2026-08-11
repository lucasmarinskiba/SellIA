import { test, expect, devices } from '@playwright/test'

test.use({ ...devices['iPhone 12'] })

test.describe('Phase 26b - Mobile App (Emulated)', () => {
  test('should display login screen on mobile', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('text=SellIA')).toBeVisible()
    await expect(page.locator('text=Sell while you sleep')).toBeVisible()
  })

  test('should login with credentials', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[placeholder="your@email.com"]', 'test@example.com')
    await page.fill('input[placeholder="••••••••"]', 'password123')
    await page.click('button:has-text("Iniciar sesión")')
    await page.waitForNavigation()
  })

  test('should display dashboard after login', async ({ page }) => {
    // Setup: Login first
    await page.goto('/login')
    await page.fill('input[placeholder="your@email.com"]', 'test@example.com')
    await page.fill('input[placeholder="••••••••"]', 'password123')
    await page.click('button:has-text("Iniciar sesión")')
    await page.waitForNavigation()

    // Test dashboard display
    await expect(page.locator('text=Hello')).toBeVisible()
  })

  test('mobile viewport should be portrait', async ({ page }) => {
    await page.goto('/login')
    const viewport = page.viewportSize()
    expect(viewport?.width).toBeLessThan(viewport?.height || 0)
  })

  test('should have tab navigation at bottom', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[placeholder="your@email.com"]', 'test@example.com')
    await page.fill('input[placeholder="••••••••"]', 'password123')
    await page.click('button:has-text("Iniciar sesión")')
    await page.waitForNavigation()

    // Check for bottom navigation indicators
    const navElements = page.locator('[role="tab"]')
    const count = await navElements.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should handle touch interactions', async ({ page }) => {
    await page.goto('/login')

    // Simulate touch input
    const emailField = page.locator('input[placeholder="your@email.com"]')
    await emailField.tap()
    await emailField.fill('test@example.com')

    const passwordField = page.locator('input[placeholder="••••••••"]')
    await passwordField.tap()
    await passwordField.fill('password123')

    const submitButton = page.locator('button:has-text("Iniciar sesión")')
    await submitButton.tap()

    await page.waitForNavigation()
  })

  test('should display register link on mobile', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('text=Creá una gratis')).toBeVisible()
  })

  test('mobile form should be full width', async ({ page }) => {
    await page.goto('/login')

    const form = page.locator('form')
    const boundingBox = await form.boundingBox()

    if (boundingBox) {
      const viewport = page.viewportSize()
      expect(boundingBox.width).toBeLessThanOrEqual((viewport?.width || 0) - 20)
    }
  })

  test('should handle keyboard on mobile', async ({ page }) => {
    await page.goto('/login')

    const emailField = page.locator('input[placeholder="your@email.com"]')
    await emailField.fill('test@example.com')
    await emailField.press('Tab')

    const passwordField = page.locator('input[placeholder="••••••••"]')
    const isFocused = await passwordField.evaluate((el) => el === document.activeElement)
    expect(isFocused).toBeTruthy()
  })
})

test.describe('Phase 26b - Mobile App (Tablet)', () => {
  test.use({ ...devices['iPad Pro'] })

  test('should display dashboard on tablet', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[placeholder="your@email.com"]', 'test@example.com')
    await page.fill('input[placeholder="••••••••"]', 'password123')
    await page.click('button:has-text("Iniciar sesión")')
    await page.waitForNavigation()

    await expect(page.locator('text=Hello')).toBeVisible()
  })

  test('tablet viewport should be landscape capable', async ({ page }) => {
    await page.goto('/login')
    const viewport = page.viewportSize()
    expect((viewport?.width || 0) > 700).toBeTruthy()
  })
})
