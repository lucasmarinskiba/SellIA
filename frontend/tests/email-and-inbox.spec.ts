import { test, expect, type BrowserContext, type Page } from '@playwright/test'

/**
 * Two flows that changed how people use SellIA, checked in a real browser:
 *  - connecting an email in two steps (address + password, then the code that arrives in that mailbox);
 *  - a Harvey prospecting thread in the unified inbox, answered from Prospección and never from the inbox.
 *
 * The backend is replaced by canned responses at the BROWSER level (page.route), so these tests need only the built
 * frontend: they say nothing about the API, they pin what the person sees and can do. Nothing here touches a real
 * mailbox, a real account or production.
 */

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000'
const NOW = new Date().toISOString()

const json = (body: unknown, status = 200) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
})

const signedIn = async (context: BrowserContext) => {
  // The middleware only checks that a session cookie exists; every API call below is answered by page.route.
  await context.addCookies([{ name: 'sellia_session', value: 'e2e', url: BASE_URL }])
}

/** Answers the calls every dashboard page makes; `extra` handles the page-specific ones first. */
const mockApi = async (page: Page, extra: (url: URL, method: string) => ReturnType<typeof json> | null) => {
  await page.route('**/api/v1/**', async (route) => {
    const req = route.request()
    const url = new URL(req.url())
    const specific = extra(url, req.method())
    if (specific) return route.fulfill(specific)
    const path = url.pathname.replace(/\/$/, '')
    if (path.endsWith('/users/me') || path.endsWith('/auth/me')) {
      return route.fulfill(json({ id: 'u1', email: 'dueno@negocio.com', full_name: 'Dueño' }))
    }
    if (path.endsWith('/businesses')) {
      return route.fulfill(json([{ id: 'b1', name: 'Panadería Sol', description: 'Pan', user_id: 'u1', is_active: true }]))
    }
    return route.fulfill(json([]))
  })
}

test.describe('Connect an email in two steps', () => {
  test('address + password, then the code, connects the mailbox', async ({ page, context }) => {
    await signedIn(context)
    const starts: unknown[] = []
    let channelsReload = 0
    await mockApi(page, (url, method) => {
      const path = url.pathname.replace(/\/$/, '')
      if (method === 'GET' && path.endsWith('/channels')) {
        channelsReload += 1
        return json([])
      }
      return null
    })
    // The start endpoint depends on the password typed, so it gets its own route (the last one registered wins).
    await page.route('**/channels/email/start', async (route) => {
      const sent = route.request().postDataJSON() as { email: string; password: string }
      starts.push(sent)
      if (sent.password === 'mala') {
        return route.fulfill(
          json({ detail: 'Gmail no aceptó el usuario o la contraseña. Gmail pide una contraseña de aplicación.' }, 422),
        )
      }
      return route.fulfill(json({ channel_id: 'c1', email: sent.email, provider: 'Gmail', expires_in: 900 }, 201))
    })
    await page.route('**/email/confirm', async (route) => {
      const { code } = route.request().postDataJSON() as { code: string }
      if (code !== '123456') return route.fulfill(json({ detail: 'Ese código no es correcto. Te quedan 4 intentos.' }, 422))
      return route.fulfill(json({ status: 'connected', email: 'ventas@gmail.com' }))
    })

    await page.goto('/dashboard/canales')
    await page.getByRole('button', { name: /conectar mi email/i }).first().click()

    // Nothing technical is asked: no server, no port, no IMAP.
    const dialog = page.getByRole('dialog')
    await expect(dialog.getByLabel('Tu email')).toBeVisible()
    await expect(dialog.getByText(/servidor|puerto|imap|smtp/i)).toHaveCount(0)

    await dialog.getByLabel('Tu email').fill('ventas@gmail.com')
    // The right help appears by itself once the provider is known.
    await expect(dialog.getByRole('link', { name: /contraseña de aplicación de gmail/i })).toBeVisible()
    await dialog.getByLabel(/contraseña de aplicación/i).first().fill('mala')
    await dialog.getByRole('button', { name: 'Enviar código' }).click()
    await expect(dialog.getByRole('alert')).toContainText('Gmail no aceptó')

    await dialog.getByLabel(/contraseña de aplicación/i).first().fill('abcd efgh ijkl mnop')
    await dialog.getByRole('button', { name: 'Enviar código' }).click()
    await expect(dialog.getByText(/te mandamos un código de 6 dígitos/i)).toBeVisible()
    await expect(dialog.getByRole('button', { name: /reenviar código \(\d+s\)/i })).toBeDisabled()

    await dialog.getByLabel('Código').fill('000000')
    await dialog.getByRole('button', { name: 'Confirmar y conectar' }).click()
    await expect(dialog.getByRole('alert')).toContainText('Te quedan 4 intentos')

    await dialog.getByLabel('Código').fill('123456')
    await dialog.getByRole('button', { name: 'Confirmar y conectar' }).click()
    await expect(page.getByText(/ventas@gmail\.com conectado/i)).toBeVisible()
    await expect(page.getByRole('dialog')).toHaveCount(0)
    expect(starts).toHaveLength(2)
    expect(channelsReload).toBeGreaterThan(1) // the list is reloaded after connecting
  })
})

test.describe('Harvey threads in the unified inbox', () => {
  const base = {
    business_id: 'b1', external_id: null, lead_email: null, lead_phone: null, status: 'active', last_message_at: NOW,
    extra_data: {}, is_active: true, created_at: NOW, updated_at: NOW, channel_connection_id: null,
    followup_count: 0, last_followup_sent_at: null,
  }
  const conversations = [
    { ...base, id: 'c1', lead_name: 'María (WhatsApp)', lead_source: 'whatsapp', platform: 'whatsapp', message_count: 2,
      last_message_preview: 'Hola, ¿tienen stock?', last_direction: 'inbound', ai_responded: true, source: 'chat', awaiting_human: false },
    { ...base, id: 'c2', lead_name: 'Ana Pérez', lead_email: 'ana@cliente.com', lead_source: 'harvey', platform: 'email',
      message_count: 3, last_message_preview: '¿Podemos hablar del precio?', last_direction: 'inbound', ai_responded: false,
      source: 'harvey', awaiting_human: true },
  ]
  const messages = [
    { id: 'm1', conversation_id: 'c2', direction: 'inbound', content: '¿Podemos hablar del precio?', content_type: 'text',
      status: 'delivered', extra_data: {}, created_at: NOW },
  ]

  test('the attention filter, the badges, and no composer on a prospecting thread', async ({ page, context }) => {
    await signedIn(context)
    await mockApi(page, (url) => {
      const path = url.pathname.replace(/\/$/, '')
      if (path.endsWith('/conversations')) return json(conversations)
      if (path.endsWith('/messages')) return json(messages)
      return null
    })

    await page.goto('/dashboard/conversaciones')
    const attention = page.getByRole('button', { name: /necesitan atención \(1\)/i })
    await expect(attention).toBeVisible()
    // The list items are buttons (the selected conversation's name also appears in the header, so target the list).
    const listItem = (name: RegExp) => page.getByRole('button', { name })
    await expect(listItem(/María \(WhatsApp\)/)).toBeVisible()

    await attention.click()
    await expect(listItem(/María \(WhatsApp\)/)).toHaveCount(0)
    await expect(listItem(/Ana Pérez/)).toBeVisible()
    await expect(page.getByText('Prospección', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('Atender', { exact: true }).first()).toBeVisible()

    await listItem(/Ana Pérez/).click()
    // The prospect is answered where Harvey's controls apply, never from here.
    await expect(page.getByPlaceholder('Escribe un mensaje...')).toHaveCount(0)
    const link = page.getByRole('link', { name: /responder en prospección/i })
    await expect(link).toBeVisible()
    await expect(link).toHaveAttribute('href', '/dashboard/prospeccion')
  })

  test('a normal chat thread keeps its composer', async ({ page, context }) => {
    await signedIn(context)
    await mockApi(page, (url) => {
      const path = url.pathname.replace(/\/$/, '')
      if (path.endsWith('/conversations')) return json([conversations[0]])
      if (path.endsWith('/messages')) return json([{ ...messages[0], conversation_id: 'c1' }])
      return null
    })
    await page.goto('/dashboard/conversaciones')
    await page.getByText('María (WhatsApp)').first().click()
    await expect(page.getByPlaceholder('Escribe un mensaje...')).toBeVisible()
    await expect(page.getByRole('link', { name: /responder en prospección/i })).toHaveCount(0)
  })
})
