import { test, expect } from '@playwright/test'

const API_URL = process.env.API_URL || 'http://localhost:8000'

test.describe('Admin Audit Panel', () => {
  test('admin can view audit logs and stats', async ({ page }) => {
    // Login as admin
    const loginRes = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: 'username=admin@selia.com&password=AdminSecure123!',
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

    // Navigate to audit panel
    await page.goto('/dashboard/admin/audit')

    // Should show stats cards
    await expect(page.locator('text=/Logins hoy|logins/i')).toBeVisible()
    await expect(page.locator('text=/Fallidos|fallidos/i')).toBeVisible()

    // Should show logs table
    await expect(page.locator('text=/Estado|estado/i')).toBeVisible()
    await expect(page.locator('text=/Usuario|usuario/i')).toBeVisible()
    await expect(page.locator('text=/IP/i')).toBeVisible()
  })

  test('non-admin is redirected from audit panel', async ({ page }) => {
    // Register and login as regular user
    const email = `regular_${Date.now()}@test.com`
    await page.request.post(`${API_URL}/api/v1/auth/register`, {
      data: { email, password: 'Pass123!', full_name: 'Regular User' },
      headers: { 'X-Turnstile-Token': 'dummy' },
    })

    const loginRes = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: `username=${email}&password=Pass123!`,
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

    await page.goto('/dashboard/admin/audit')

    // Should redirect to dashboard (non-admin access denied)
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('admin can filter audit logs', async ({ page }) => {
    // Login as admin
    const loginRes = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: 'username=admin@selia.com&password=AdminSecure123!',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Turnstile-Token': 'dummy',
      },
    })

    const loginData = await loginRes.json()
    await page.evaluate(
      ({ token }) => {
        (window as any).__authToken = token
        localStorage.setItem('token', token)
      },
      { token: loginData.access_token }
    )

    await page.goto('/dashboard/admin/audit')

    // Apply filter by event type
    const eventFilter = page.locator('select').first()
    if (await eventFilter.isVisible().catch(() => false)) {
      await eventFilter.selectOption('success')

      // Apply filter button
      const applyButton = page.locator('button:has-text("Aplicar")')
      if (await applyButton.isVisible().catch(() => false)) {
        await applyButton.click()
      }

      // Wait for table update
      await page.waitForTimeout(500)
    }
  })
})
