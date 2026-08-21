const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    // Configurable: BACKEND_ORIGIN permite apuntar a localhost en dev o a la
    // API pública en cloud. BACKEND_URL es el nombre usado en Vercel.
    // Sin ninguno de los dos seteados (ej. build local sin backend externo),
    // no reescribe /api/* y deja pasar la request (evita DNS_HOSTNAME_NOT_FOUND).
    const backend = process.env.BACKEND_ORIGIN || process.env.BACKEND_URL
    if (!backend) {
      return []
    }
    return [
      {
        source: '/api/:path*',
        destination: `${backend}/api/:path*`,
      },
    ]
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
