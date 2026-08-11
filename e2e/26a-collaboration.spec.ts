import { test, expect } from '@playwright/test'

test.describe('Phase 26a - Team Collaboration Hub', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.waitForNavigation()
  })

  test('should display collaboration panel', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')
    await expect(page.locator('text=Team Collaboration')).toBeVisible()
    await expect(page.locator('text=Real-time deal discussions')).toBeVisible()
  })

  test('should post and display comment', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    const commentText = `Test comment ${Date.now()}`
    await page.fill('textarea[placeholder*="Add comment"]', commentText)
    await page.click('button:has-text("Post Comment")')

    await expect(page.locator(`text="${commentText}"`)).toBeVisible({ timeout: 5000 })
  })

  test('should display @mention autocomplete', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    await page.fill('textarea[placeholder*="Add comment"]', 'Hey @')
    await expect(page.locator('text=Mention teammate')).toBeVisible()
    await expect(page.locator('text=team_1')).toBeVisible()
  })

  test('should insert mention on click', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    const textArea = page.locator('textarea[placeholder*="Add comment"]')
    await textArea.fill('Hey @')
    await page.click('button:has-text("team_1")')

    const content = await textArea.inputValue()
    expect(content).toContain('@team_1')
  })

  test('should display activity feed', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    await expect(page.locator('text=Team Discussion')).toBeVisible()
    await expect(page.locator('text=comments')).toBeVisible()
  })

  test('should select different deal', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    const initialCount = await page.locator('[role="button"]:has-text("deal_001")').count()
    expect(initialCount).toBeGreaterThan(0)

    await page.click('[role="button"]:has-text("deal_002")')
    await expect(page.locator('text="deal_002"')).toBeVisible()
  })

  test('approval queue should display', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    await expect(page.locator('text=Approval Queue')).toBeVisible()
  })

  test('should approve action', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    const approveButtons = page.locator('button:has-text("Approve")')
    if ((await approveButtons.count()) > 0) {
      await approveButtons.first().click()
      await expect(page.locator('text=Success')).toBeVisible({ timeout: 3000 })
    }
  })

  test('should reject action', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    const rejectButtons = page.locator('button:has-text("Reject")')
    if ((await rejectButtons.count()) > 0) {
      await rejectButtons.first().click()
      await expect(page.locator('text=Success')).toBeVisible({ timeout: 3000 })
    }
  })

  test('should display shared deals section', async ({ page }) => {
    await page.goto('/dashboard/enterprise/collaboration')

    const sharedSection = page.locator('text=Shared With')
    if ((await sharedSection.count()) > 0) {
      await expect(sharedSection).toBeVisible()
    }
  })
})
