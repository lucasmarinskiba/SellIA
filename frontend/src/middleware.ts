import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Rutas protegidas que requieren autenticación
const PROTECTED_ROUTES = ['/dashboard', '/settings', '/profile', '/admin']

// Rutas públicas (no redirigir si ya está autenticado)
const PUBLIC_ONLY_ROUTES = ['/login', '/register']

// Root + reserved subdomains that should NOT be treated as tenant subdomains
const RESERVED_HOSTS = new Set([
  'sellia.app', 'www.sellia.app', 'app.sellia.app', 'api.sellia.app',
  'docs.sellia.app', 'blog.sellia.app', 'status.sellia.app',
  'localhost', 'localhost:3000', 'localhost:56621',
])

/**
 * Extract tenant subdomain from host header.
 * Returns null if root / reserved / non-tenant host.
 */
function extractTenantSubdomain(host: string | null): string | null {
  if (!host) return null
  const h = host.toLowerCase().split(':')[0]
  if (RESERVED_HOSTS.has(host.toLowerCase()) || RESERVED_HOSTS.has(h)) return null
  // Must be {sub}.sellia.app (3 parts) and sub not reserved
  if (h.endsWith('.sellia.app')) {
    const sub = h.replace('.sellia.app', '')
    if (sub.includes('.')) return null  // multi-level not supported
    if (['www', 'app', 'api', 'docs', 'blog', 'status'].includes(sub)) return null
    return sub
  }
  return null
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const host = request.headers.get('host')

  // ─── Tenant subdomain routing ───
  // {tenant}.sellia.app → set x-tenant-subdomain header for downstream + rewrite
  const tenantSub = extractTenantSubdomain(host)
  if (tenantSub) {
    const url = request.nextUrl.clone()
    // Pass through to same path · attach header for components to read
    const res = NextResponse.next({
      request: {
        headers: new Headers({ ...Object.fromEntries(request.headers), 'x-tenant-subdomain': tenantSub }),
      },
    })
    res.headers.set('x-tenant-subdomain', tenantSub)
    res.cookies.set('sellia.tenant', tenantSub, { path: '/', sameSite: 'lax', httpOnly: false })
    // Apply security headers below by falling through · but need to return at end
    applySecurityHeaders(res, request)
    return res
  }

  // Headers de seguridad HTTP para todas las respuestas
  const response = NextResponse.next()
  applySecurityHeaders(response, request)

  // Verificar autenticación vía cookie httpOnly
  const token = request.cookies.get('access_token')?.value
  const isProtected = PROTECTED_ROUTES.some((route) => pathname.startsWith(route))
  const isPublicOnly = PUBLIC_ONLY_ROUTES.some((route) => pathname === route)

  if (isProtected && !token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (isPublicOnly && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return response
}

function applySecurityHeaders(response: NextResponse, request: NextRequest): void {
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set(
    'Permissions-Policy',
    'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()'
  )
  response.headers.set('X-DNS-Prefetch-Control', 'on')
  response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload')
  response.headers.set('X-XSS-Protection', '1; mode=block')

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  response.headers.set(
    'Content-Security-Policy',
    `default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; font-src 'self' data:; connect-src 'self' ${apiUrl}; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests;`
  )
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.svg|.*\\.png|.*\\.jpg).*)'],
}
