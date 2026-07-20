import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';

test.describe('SellIA E2E Tests', () => {
  // Test 1: User Login Flow
  test('should complete login flow successfully', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`);

    // Wait for login form
    await page.waitForSelector('input[type="email"]');

    // Fill credentials
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'TestPassword123!');

    // Submit login
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await page.waitForURL(`${FRONTEND_URL}/dashboard`);
    expect(page.url()).toContain('/dashboard');
  });

  // Test 2: Market Detection Flow
  test('should detect market and suggest strategies', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);

    // Navigate to market detection
    await page.click('text=Detect Market');
    await page.waitForSelector('input[placeholder="Enter market URL or description"]');

    // Input market data
    await page.fill('input[placeholder="Enter market URL or description"]', 'E-commerce AI tools');

    // Submit detection
    await page.click('button:has-text("Analyze Market")');

    // Wait for results
    await page.waitForSelector('.market-analysis-results');

    // Verify market analysis completed
    const marketName = await page.textContent('.market-name');
    expect(marketName).toBeTruthy();

    // Verify strategies suggested
    const strategies = await page.locator('.strategy-card').count();
    expect(strategies).toBeGreaterThan(0);
  });

  // Test 3: Strategy Selection Flow
  test('should select and configure strategy', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard/strategies`);

    // Wait for strategy list
    await page.waitForSelector('.strategy-card');

    // Select first strategy
    await page.click('.strategy-card:first-child');

    // Verify strategy details page
    await page.waitForSelector('.strategy-details');
    expect(page.url()).toContain('/strategies/');

    // Configure strategy
    await page.fill('input[name="budget"]', '1000');
    await page.fill('input[name="daily_limit"]', '100');

    // Activate strategy
    await page.click('button:has-text("Activate Strategy")');

    // Verify activation
    await page.waitForSelector('text=Strategy activated');
    expect(await page.textContent('text=Strategy activated')).toBeTruthy();
  });

  // Test 4: Computer Use Automation Flow
  test('should execute computer use automation', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard/automations`);

    // Create new automation
    await page.click('button:has-text("New Automation")');
    await page.waitForSelector('.automation-form');

    // Fill automation details
    await page.fill('input[name="name"]', 'Email Campaign');
    await page.fill('input[name="description"]', 'Automated email outreach');

    // Select computer use task
    await page.click('select[name="task_type"]');
    await page.click('option[value="email_campaign"]');

    // Configure parameters
    await page.fill('input[name="recipient_list"]', 'leads.csv');
    await page.fill('input[name="email_template"]', 'sales_pitch');

    // Schedule automation
    await page.click('input[type="datetime-local"][name="schedule"]');
    await page.keyboard.type('2024-01-15T09:00');

    // Submit
    await page.click('button:has-text("Create Automation")');

    // Verify creation
    await page.waitForSelector('text=Automation created successfully');
    expect(page.url()).toContain('/automations/');
  });

  // Test 5: Payment Processing Flow
  test('should process payment successfully', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard/billing`);

    // Upgrade plan
    await page.click('button:has-text("Upgrade to Pro")');
    await page.waitForSelector('.payment-modal');

    // Fill stripe test card
    const frameHandle = await page.$('iframe[title*="Stripe"]');
    const frame = await frameHandle.contentFrame();

    // Card details (Stripe test card)
    await frame.fill('input[name="cardnumber"]', '4242424242424242');
    await frame.fill('input[name="exp-date"]', '12/25');
    await frame.fill('input[name="cvc"]', '123');
    await frame.fill('input[name="postal"]', '12345');

    // Submit payment
    await page.click('button:has-text("Pay Now")');

    // Verify payment success
    await page.waitForSelector('text=Payment successful');
    expect(await page.textContent('text=Your plan has been upgraded')).toBeTruthy();
  });

  // Test 6: Dashboard KPI Updates
  test('should update dashboard KPIs in real-time', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);

    // Wait for KPI widgets
    await page.waitForSelector('.kpi-widget');

    // Get initial values
    const initialRevenue = await page.textContent('.kpi-revenue');
    const initialLeads = await page.textContent('.kpi-leads');

    // Simulate data update by waiting
    await page.waitForTimeout(5000);

    // Refresh data
    await page.click('button[aria-label="Refresh KPIs"]');

    // Wait for update
    await page.waitForLoadState('networkidle');

    // Verify values updated
    const updatedRevenue = await page.textContent('.kpi-revenue');
    expect(updatedRevenue).not.toBe(initialRevenue);
  });

  // Test 7: Real-time WebSocket Updates
  test('should receive real-time WebSocket updates', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);

    // Listen for WebSocket messages
    let websocketMessage = null;
    page.on('websocket', ws => {
      ws.on('framesent', event => {
        websocketMessage = event;
      });
    });

    // Wait for WebSocket connection
    await page.waitForTimeout(2000);

    // Verify WebSocket connected
    const wsStatus = await page.textContent('.ws-status');
    expect(wsStatus).toContain('Connected');

    // Trigger event that sends WebSocket message
    await page.click('button:has-text("Send Test Update")');

    // Wait for message
    await page.waitForTimeout(1000);
    expect(websocketMessage).not.toBeNull();
  });

  // Test 8: Error Handling
  test('should handle errors gracefully', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);

    // Try invalid action
    const response = await page.evaluate(() =>
      fetch('/api/invalid-endpoint').then(r => r.status)
    );

    expect(response).toBe(404);

    // Verify error message displayed
    await page.goto(`${FRONTEND_URL}/dashboard/invalid-page`);
    await page.waitForSelector('text=Page not found');
    expect(page.url()).toContain('invalid-page');
  });

  // Test 9: Data Persistence
  test('should persist user data across sessions', async ({ page, context }) => {
    // First session
    await page.goto(`${FRONTEND_URL}/dashboard`);
    await page.click('text=Settings');
    await page.fill('input[name="company_name"]', 'Test Company');
    await page.click('button:has-text("Save")');
    await page.waitForSelector('text=Settings saved');

    // Close browser context
    await context.close();

    // New session
    const newPage = await context.newPage();
    await newPage.goto(`${FRONTEND_URL}/dashboard/settings`);

    // Verify data persisted
    const companyName = await newPage.inputValue('input[name="company_name"]');
    expect(companyName).toBe('Test Company');
  });

  // Test 10: Performance - Page Load Time
  test('should load dashboard within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${FRONTEND_URL}/dashboard`);
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Dashboard should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  // Test 11: Accessibility
  test('should meet accessibility standards', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);

    // Check for accessibility issues using axe
    const violations = await page.evaluate(() => {
      // This assumes axe-core is loaded
      return (window as any).axe.run();
    }).catch(() => ({ violations: [] }));

    // Allow some minor violations but catch critical ones
    const criticalViolations = violations?.violations?.filter(
      (v: any) => v.impact === 'critical'
    ) || [];

    expect(criticalViolations).toHaveLength(0);
  });

  // Test 12: Multi-user Collaboration
  test('should support multiple concurrent users', async ({ browser }) => {
    // Create multiple browser contexts
    const contexts = await Promise.all([
      browser.newContext(),
      browser.newContext(),
      browser.newContext(),
    ]);

    const pages = await Promise.all(
      contexts.map(ctx => ctx.newPage())
    );

    // All users navigate to dashboard
    await Promise.all(
      pages.map(p => p.goto(`${FRONTEND_URL}/dashboard`))
    );

    // Verify all loaded
    for (const page of pages) {
      await page.waitForSelector('.dashboard-content');
      expect(page.url()).toContain('/dashboard');
    }

    // Clean up
    await Promise.all(
      contexts.map(ctx => ctx.close())
    );
  });
});

// API Tests
test.describe('SellIA API Tests', () => {
  // Test API endpoints directly
  test('should return 200 on /api/health', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);
    expect(response.status()).toBe(200);
  });

  test('should authenticate with JWT token', async ({ request }) => {
    const loginResponse = await request.post(`${API_URL}/api/auth/login`, {
      data: {
        email: 'test@example.com',
        password: 'TestPassword123!',
      },
    });

    const data = await loginResponse.json();
    expect(data.access_token).toBeTruthy();
  });

  test('should handle rate limiting', async ({ request }) => {
    // Make multiple rapid requests
    const promises = Array(70).fill(null).map(() =>
      request.get(`${API_URL}/api/data`)
    );

    const responses = await Promise.all(promises);

    // Some should be rate limited
    const rateLimited = responses.filter(r => r.status() === 429);
    expect(rateLimited.length).toBeGreaterThan(0);
  });
});
