import { test, expect } from '@playwright/test'

const API_URL = process.env.API_URL || 'http://localhost:8000'

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Seed a test user via API before each test
    const email = `e2e_${Date.now()}@test.com`
    const password = 'TestPass123!'

    await page.request.post(`${API_URL}/api/v1/auth/register`, {
      data: { email, password, full_name: 'E2E Test' },
      headers: { 'X-Turnstile-Token': 'dummy' },
    })

    // Store credentials for tests
    await page.evaluate(
      ({ e, p }) => {
        ;(window as any).__testEmail = e
        ;(window as any).__testPassword = p
      },
      { e: email, p: password }
    )
  })

  test('user can register and login', async ({ page }) => {
    const email = `register_${Date.now()}@test.com`
    const password = 'RegisterPass123!'

    await page.goto('/register')
    await expect(page).toHaveURL(/\/register/)

    // Fill registration form
    await page.getByPlaceholder(/tu@email.com/i).fill(email)
    await page.getByPlaceholder(/contraseña/i).first().fill(password)
    await page.getByPlaceholder(/nombre completo/i).fill('E2E Register Test')

    await page.getByRole('button', { name: /registrarme|crear cuenta/i }).click()

    // Should redirect to login or dashboard
    await expect(page).toHaveURL(/\/(login|dashboard)/, { timeout: 10000 })
  })

  test('user can login and see dashboard', async ({ page }) => {
    const creds = await page.evaluate(() => ({
      email: (window as any).__testEmail,
      password: (window as any).__testPassword,
    }))

    await page.goto('/login')
    await page.getByPlaceholder(/tu@email.com/i).fill(creds.email)
    await page.getByPlaceholder(/contraseña/i).fill(creds.password)
    await page.getByRole('button', { name: /iniciar sesión/i }).click()

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })
    await expect(page.locator('text=/dashboard/i').or(page.locator('text=Dashboard'))).toBeVisible()
  })

  test('login with wrong password shows error', async ({ page }) => {
    const creds = await page.evaluate(() => ({
      email: (window as any).__testEmail,
      password: (window as any).__testPassword,
    }))

    await page.goto('/login')
    await page.getByPlaceholder(/tu@email.com/i).fill(creds.email)
    await page.getByPlaceholder(/contraseña/i).fill('WrongPassword123!')
    await page.getByRole('button', { name: /iniciar sesión/i }).click()

    await expect(page.locator('text=/incorrectos|Credenciales/i')).toBeVisible()
  })

  test('user can logout', async ({ page }) => {
    const creds = await page.evaluate(() => ({
      email: (window as any).__testEmail,
      password: (window as any).__testPassword,
    }))

    // Login first
    await page.goto('/login')
    await page.getByPlaceholder(/tu@email.com/i).fill(creds.email)
    await page.getByPlaceholder(/contraseña/i).fill(creds.password)
    await page.getByRole('button', { name: /iniciar sesión/i }).click()
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })

    // Logout
    await page.goto('/logout')
    await expect(page).toHaveURL(/\/login/)
  })
})
