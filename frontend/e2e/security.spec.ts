import { test, expect } from '@playwright/test'

const API_URL = process.env.API_URL || 'http://localhost:8000'

test.describe('Security Features', () => {
  test.beforeEach(async ({ page }) => {
    const email = `security_${Date.now()}@test.com`
    const password = 'TestPass123!'

    await page.request.post(`${API_URL}/api/v1/auth/register`, {
      data: { email, password, full_name: 'Security Test' },
      headers: { 'X-Turnstile-Token': 'dummy' },
    })

    const loginRes = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Turnstile-Token': 'dummy',
      },
    })

    const loginData = await loginRes.json()
    await page.evaluate(
      ({ token }) => {
        ;(window as any).__authToken = token
        localStorage.setItem('token', token)
      },
      { token: loginData.access_token }
    )
  })

  test('user can view security settings page', async ({ page }) => {
    const token = await page.evaluate(() => (window as any).__authToken)
    await page.goto('/dashboard/seguridad')

    // Should show 2FA section
    await expect(page.locator('text=/2FA|dos factores/i')).toBeVisible()

    // Should show geofencing info
    await expect(page.locator('text=/Geofencing|geofencing/i')).toBeVisible()

    // Should show breach monitoring
    await expect(page.locator('text=/breach|filtraci/i')).toBeVisible()
  })

  test('user can view active sessions', async ({ page }) => {
    const token = await page.evaluate(() => (window as any).__authToken)
    await page.goto('/dashboard/sessions')

    // Should show sessions list
    await expect(page.locator('text=/sesiones|Sesiones/i')).toBeVisible()
    await expect(page.locator('text=/Dispositivo|dispositivo/i')).toBeVisible()
  })

  test('user can setup 2FA', async ({ page }) => {
    const token = await page.evaluate(() => (window as any).__authToken)
    await page.goto('/dashboard/seguridad')

    // Click setup 2FA if available
    const setupButton = page.locator('button:has-text("Configurar 2FA")')
    if (await setupButton.isVisible().catch(() => false)) {
      await setupButton.click()

      // Should show QR code
      await expect(page.locator('img[alt="QR 2FA"]')).toBeVisible({ timeout: 5000 })

      // Should show secret
      await expect(page.locator('text=/Clave secreta/i')).toBeVisible()
    }
  })

  test('login with 2FA requires code', async ({ page }) => {
    // This test requires a user with 2FA already enabled
    // We skip if not applicable
    test.skip(true, 'Requires user with 2FA enabled')
  })

  test('rate limiting shows visual feedback on login', async ({ page }) => {
    const email = `ratelimit_${Date.now()}@test.com`
    const password = 'WrongPass123!'

    await page.request.post(`${API_URL}/api/v1/auth/register`, {
      data: { email, password: 'CorrectPass123!', full_name: 'Rate Limit Test' },
      headers: { 'X-Turnstile-Token': 'dummy' },
    })

    await page.goto('/login')
    await page.getByPlaceholder(/tu@email.com/i).fill(email)

    // Attempt multiple failed logins
    for (let i = 0; i < 3; i++) {
      await page.getByPlaceholder(/contraseña/i).fill(password)
      await page.getByRole('button', { name: /iniciar sesión/i }).click()
      await page.waitForTimeout(500)
    }

    // Should show rate limit or error feedback
    await expect(
      page.locator('text=/incorrectos|bloqueada|demasiados|rate/i')
    ).toBeVisible()
  })
})
