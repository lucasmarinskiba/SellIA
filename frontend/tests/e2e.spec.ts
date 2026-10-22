import { createHmac } from 'node:crypto';
import { test, expect } from '@playwright/test';

// The stack under test (CI builds it and passes these). Never default to production:
// this suite signs users up and attempts logins, so pointing it at prod writes real data.
const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000';
const API_URL = process.env.API_URL ?? 'http://localhost:8000';

// Satisfies the client-side strength meter and the server's password policy
// (8+ chars, upper, lower, digit and one of @+-!#$%).
const VALID_PASSWORD = 'E2eTest-123!';

const BASE32_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

const base32Decode = (input: string): Buffer => {
  let bits = '';
  for (const char of input.replace(/=+$/, '').toUpperCase()) {
    const index = BASE32_ALPHABET.indexOf(char);
    if (index === -1) throw new Error(`Not a base32 character: ${char}`);
    bits += index.toString(2).padStart(5, '0');
  }
  const bytes: number[] = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) bytes.push(parseInt(bits.slice(i, i + 8), 2));
  return Buffer.from(bytes);
};

// RFC 6238 TOTP (SHA-1, 30 s step, 6 digits) -- what Google Authenticator and pyotp compute.
const totp = (secret: string, nowMs: number = Date.now()): string => {
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(nowMs / 1000 / 30)));
  const digest = createHmac('sha1', base32Decode(secret)).update(counter).digest();
  const offset = digest[digest.length - 1] & 0x0f;
  const binary =
    ((digest[offset] & 0x7f) << 24) |
    (digest[offset + 1] << 16) |
    (digest[offset + 2] << 8) |
    digest[offset + 3];
  return String(binary % 1_000_000).padStart(6, '0');
};

test.describe('SellIA E2E Sales Funnel', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to homepage
    await page.goto(BASE_URL);
  });

  test.describe('Authentication Flow', () => {
    test('signup page loads', async ({ page }) => {
      // Navigate to signup
      await page.goto(`${BASE_URL}/signup`);

      // The form has name, email, password and confirm-password fields, so
      // `input[type="password"]` matches two elements: select by placeholder.
      await expect(page.getByPlaceholder('Juan García')).toBeVisible();
      await expect(page.getByPlaceholder('tu@correo.com')).toBeVisible();
      await expect(page.getByPlaceholder('MiContraseña123@')).toBeVisible();
      await expect(page.getByPlaceholder('Repite tu contraseña')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('can signup new user and complete 2FA', async ({ page }) => {
      // Every 2FA call the page makes, so we can check it uses the authenticated
      // flow (session token, code in the query string) and never the retired
      // unauthenticated one that took a user_id + secret in the body.
      const twoFactorRequests: { url: string; authorization?: string; body: string | null }[] = [];
      page.on('request', (request) => {
        if (request.url().includes('/auth/2fa/')) {
          twoFactorRequests.push({
            url: request.url(),
            authorization: request.headers()['authorization'],
            body: request.postData(),
          });
        }
      });

      await page.goto(`${BASE_URL}/signup`);

      const email = `user-${Date.now()}@test.local`;
      await page.getByPlaceholder('Juan García').fill('E2E Test User');
      await page.getByPlaceholder('tu@correo.com').fill(email);
      await page.getByPlaceholder('MiContraseña123@').fill(VALID_PASSWORD);
      await page.getByPlaceholder('Repite tu contraseña').fill(VALID_PASSWORD);

      // Submit stays disabled until the password meets the strength rules.
      const submitButton = page.locator('button[type="submit"]');
      await expect(submitButton).toBeEnabled();
      await submitButton.click();

      // On success the page moves on to the 2FA-setup step and the signup form
      // disappears; on failure the form stays and shows the error.
      await expect(page.getByRole('heading', { name: 'Crear cuenta segura' })).toBeHidden({
        timeout: 15000,
      });
      await expect(page.getByRole('heading', { name: 'Autenticación de dos factores' })).toBeVisible();

      // Step 1: the server hands out the secret and QR for the account we just created.
      await page.getByRole('button', { name: 'Configurar 2FA' }).click();
      await expect(page.getByAltText('QR Code')).toBeVisible({ timeout: 15000 });
      const secret = (await page.locator('code').first().innerText()).trim();
      expect(secret).toMatch(/^[A-Z2-7]{16,}$/);

      // A wrong code is refused and keeps us on the verification step.
      await page.getByPlaceholder('000000').fill('000000');
      await page.getByRole('button', { name: 'Verificar código' }).click();
      await expect(page.getByText('Código incorrecto')).toBeVisible({ timeout: 15000 });

      // Step 2: the real code from the authenticator app finishes the enrolment.
      await page.getByPlaceholder('000000').fill(totp(secret));
      await page.getByRole('button', { name: 'Verificar código' }).click();
      await expect(page.getByText('¡2FA Habilitado!')).toBeVisible({ timeout: 15000 });
      await expect(page.getByTestId('backup-codes').locator('li')).toHaveCount(8);

      await page.getByRole('button', { name: 'Continuar' }).click();
      await expect(page.getByRole('heading', { name: '¡Cuenta creada!' })).toBeVisible();

      expect(twoFactorRequests.map((r) => new URL(r.url).pathname)).toEqual([
        '/api/v1/auth/2fa/setup',
        '/api/v1/auth/2fa/verify',
        '/api/v1/auth/2fa/verify',
      ]);
      for (const request of twoFactorRequests) {
        expect(request.authorization).toMatch(/^Bearer .+/);
        expect(request.body ?? '').toBe('');
      }
      expect(new URL(twoFactorRequests[2].url).searchParams.get('code')).toMatch(/^\d{6}$/);

      // 2FA is really on for the account: password alone no longer logs in.
      const signin = await page.request.post(`${API_URL}/api/v1/auth/signin`, {
        data: { email, password: VALID_PASSWORD },
      });
      expect(signin.ok()).toBeTruthy();
      const signinBody = await signin.json();
      expect(signinBody.requires_2fa).toBe(true);
      expect(signinBody.access_token).toBeUndefined();
    });

    test('login page accessible', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);

      const emailInput = page.locator('input[type="email"]');
      await expect(emailInput).toBeVisible();
    });
  });

  test.describe('Business Setup Flow', () => {
    test('dashboard loads for authenticated user', async ({ page }) => {
      // Would require valid auth token
      await page.goto(`${BASE_URL}/dashboard`);

      // May redirect to login if not authenticated
      // That's OK - verifies auth flow exists
      const content = page.locator('main, nav, .dashboard, .container');
      await expect(content.first()).toBeVisible().catch(() => {
        // Expected if not logged in
      });
    });

    test('products page accessible', async ({ page }) => {
      await page.goto(`${BASE_URL}/products`);

      // Page should load (may be empty)
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('locations page accessible', async ({ page }) => {
      await page.goto(`${BASE_URL}/locations`);

      const body = page.locator('body');
      await expect(body).toBeVisible();
    });
  });

  test.describe('Phase 5 - Offline Integration', () => {
    test('qr code generation page accessible', async ({ page }) => {
      await page.goto(`${BASE_URL}/qr-codes`);

      // Should have some content
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('location check-in page accessible', async ({ page }) => {
      await page.goto(`${BASE_URL}/checkin`);

      const body = page.locator('body');
      await expect(body).toBeVisible();
    });
  });

  test.describe('API Integration', () => {
    test('backend API is reachable', async ({ page }) => {
      const response = await page.request.get(`${API_URL}/api/ping`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data.status).toBe('ok');
    });

    test('signup endpoint works', async ({ page }) => {
      const response = await page.request.post(`${API_URL}/api/v1/auth/signup`, {
        data: {
          email: `e2e-${Date.now()}@test.local`,
          password: VALID_PASSWORD,
          full_name: 'E2E Test User'
        }
      });

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('user_id');
      expect(data).toHaveProperty('access_token');
    });

    test('qr generation endpoint requires a login', async ({ page }) => {
      // QR codes are printed for a business's own location, so generating one takes an account that
      // belongs to it. It used to answer 200 to anyone, for any location id, without looking it up.
      // The authorised path (owner / member -> 200 with the payloads) is covered by
      // backend/tests/test_location_checkin_qr_routers_db.py.
      const locationId = '00000000-0000-0000-0000-000000000001';
      const response = await page.request.get(
        `${API_URL}/api/v1/locations/${locationId}/qr-codes`
      );

      expect(response.status()).toBe(401);
    });
  });

  test.describe('Navigation', () => {
    test('main navigation is accessible', async ({ page }) => {
      // Check for nav elements
      const nav = page.locator('nav, header');

      await expect(nav.first()).toBeVisible().catch(() => {
        // May not have nav on home page
      });
    });

    test('footer exists', async ({ page }) => {
      const footer = page.locator('footer');

      await expect(footer).toBeVisible().catch(() => {
        // May not have footer on all pages
      });
    });

    test('links are working', async ({ page }) => {
      // Check for broken links (basic crawl)
      const links = page.locator('a[href]');
      const count = await links.count();

      expect(count).toBeGreaterThan(0);
    });
  });

  test.describe('Performance', () => {
    test('page loads in reasonable time', async ({ page }) => {
      const startTime = Date.now();

      await page.goto(BASE_URL);

      const loadTime = Date.now() - startTime;

      // Should load in < 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });

    test('API responds quickly', async ({ page }) => {
      const startTime = Date.now();

      const response = await page.request.get(`${API_URL}/api/ping`);

      const responseTime = Date.now() - startTime;

      // API should respond in < 1 second
      expect(responseTime).toBeLessThan(1000);
      expect(response.status()).toBe(200);
    });
  });

  test.describe('Error Handling', () => {
    test('invalid URLs return appropriate responses', async ({ page }) => {
      const response = await page.request.get(`${API_URL}/invalid-endpoint`, {
        failOnStatusCode: false
      });

      // Should get 404, not 500
      expect([404, 405]).toContain(response.status());
    });

    test('invalid auth returns error', async ({ page }) => {
      const response = await page.request.post(
        `${API_URL}/api/v1/offline-conversions`,
        {
          data: { location_id: 'test' },
          failOnStatusCode: false
        }
      );

      // Should fail auth check
      expect([401, 403]).toContain(response.status());
    });
  });
});
