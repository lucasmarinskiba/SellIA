import { Page } from '@playwright/test'

export async function loginAsTestUser(page: Page): Promise<void> {
  await page.goto('/login')
  await page.fill('input[type="email"]', 'test@example.com')
  await page.fill('input[type="password"]', 'password123')
  await page.click('button[type="submit"]')
  await page.waitForNavigation()
}

export async function navigateToDashboard(page: Page): Promise<void> {
  await loginAsTestUser(page)
  await page.goto('/dashboard')
}

export async function navigateToCollaboration(page: Page): Promise<void> {
  await loginAsTestUser(page)
  await page.goto('/dashboard/enterprise/collaboration')
}

export async function navigateToIntelligence(page: Page): Promise<void> {
  await loginAsTestUser(page)
  await page.goto('/dashboard/enterprise/intelligence')
}

export async function getRandomDealId(): string {
  return `deal_${Math.floor(Math.random() * 1000)}`
}

export async function getRandomUserId(): string {
  return `user_${Math.floor(Math.random() * 1000)}`
}

export async function waitForElement(page: Page, selector: string, timeout: number = 5000): Promise<boolean> {
  try {
    await page.waitForSelector(selector, { timeout })
    return true
  } catch {
    return false
  }
}

export async function takeScreenshot(page: Page, name: string): Promise<void> {
  await page.screenshot({ path: `screenshots/${name}.png` })
}

export interface TestResult {
  passed: number
  failed: number
  skipped: number
  duration: number
}

export async function generateTestReport(results: TestResult): Promise<string> {
  return `
Test Report
===========
Passed:  ${results.passed}
Failed:  ${results.failed}
Skipped: ${results.skipped}
Duration: ${results.duration}ms

Status: ${results.failed === 0 ? '✅ PASS' : '❌ FAIL'}
  `.trim()
}
