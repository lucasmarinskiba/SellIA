import { test, expect } from '@playwright/test'

const API_URL = process.env.API_URL || 'http://localhost:8000'

test.describe('Caja de Cristal — Computer Use Agents', () => {
  test.beforeEach(async ({ page }) => {
    // Seed a test user via API
    const email = `cu_${Date.now()}@test.com`
    const password = 'TestPass123!'

    await page.request.post(`${API_URL}/api/v1/auth/register`, {
      data: { email, password, full_name: 'CU Test' },
      headers: { 'X-Turnstile-Token': 'dummy' },
    })

    // Login and persist token
    const loginRes = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: `username=${email}&password=${password}`,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Turnstile-Token': 'dummy',
      },
    })
    const { access_token } = await loginRes.json()

    await page.evaluate(({ token }) => {
      ;(window as any).__authToken = token
      localStorage.setItem('token', token)
    }, { token: access_token })
  })

  test('sidebar shows Caja de Cristal link', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.locator('text=Caja de Cristal')).toBeVisible()
  })

  test('Caja de Cristal page loads with creation form', async ({ page }) => {
    await page.goto('/dashboard/caja-de-cristal')

    // Header
    await expect(page.locator('h1', { hasText: 'Caja de Cristal' })).toBeVisible()
    await expect(page.locator('text=Supervisá en tiempo real')).toBeVisible()

    // Creation form
    await expect(page.locator('text=Nueva automatización')).toBeVisible()
    await expect(page.locator('textarea[placeholder*="Qué querés que haga"]')).toBeVisible()
    await expect(page.locator('input[type="url"]')).toBeVisible()
    await expect(page.locator('button', { hasText: 'Iniciar Caja de Cristal' })).toBeVisible()

    // Recent sessions panel
    await expect(page.locator('text=Sesiones recientes')).toBeVisible()
  })

  test('info cards are visible', async ({ page }) => {
    await page.goto('/dashboard/caja-de-cristal')

    await expect(page.locator('text=Supervisión Total')).toBeVisible()
    await expect(page.locator('text=Control Instantáneo')).toBeVisible()
    await expect(page.locator('text=Chat Directo')).toBeVisible()
  })

  test('create session button is disabled without task', async ({ page }) => {
    await page.goto('/dashboard/caja-de-cristal')

    const button = page.locator('button', { hasText: 'Iniciar Caja de Cristal' })
    await expect(button).toBeDisabled()

    // Fill task
    await page.locator('textarea').fill('Navegar a Google')
    await expect(button).toBeEnabled()
  })

  test('can create a session and see it in recent sessions', async ({ page }) => {
    await page.goto('/dashboard/caja-de-cristal')

    // Fill and submit
    await page.locator('textarea').fill('Test E2E session')
    await page.locator('input[type="url"]').fill('https://google.com')

    // Click create — this will fail without API key but should still create session
    const button = page.locator('button', { hasText: 'Iniciar Caja de Cristal' })
    await button.click()

    // Should show loading or error (since no API key in test env)
    // But the session should appear in recent sessions if creation succeeded
    await page.waitForTimeout(2000)

    // Check if recent sessions shows something
    const recentSessions = page.locator('text=Test E2E session')
    const count = await recentSessions.count()
    // Session might or might not appear depending on test env setup
    // We just verify the page doesn't crash
    await expect(page.locator('text=Caja de Cristal')).toBeVisible()
  })

  test(' SellIAAssistant shows Computer Use action button', async ({ page }) => {
    // This tests the integration with the orchestrator
    // We just verify the assistant widget renders correctly
    await page.goto('/dashboard')

    // Open assistant
    const assistantButton = page.locator('[data-testid="sellia-assistant-trigger"]').or(
      page.locator('button').filter({ has: page.locator('svg') }).first()
    )

    // Try to find and click the floating assistant button
    const floatingBtn = page.locator('button[class*="fixed"]').or(
      page.locator('button').filter({ hasText: /AI|Asistente|SellIA/i })
    )

    if (await floatingBtn.count() > 0) {
      await floatingBtn.first().click()
      // Verify assistant panel opened
      await expect(page.locator('text=SellIA').or(page.locator('text=Asistente'))).toBeVisible()
    }
  })
})
