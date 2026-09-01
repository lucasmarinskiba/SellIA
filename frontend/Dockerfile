# Debian (glibc), not Alpine (musl), for the builder stage: tailwindcss v4's
# @tailwindcss/oxide is a Rust native addon shipped as per-platform optional
# dependencies (@tailwindcss/oxide-linux-x64-musl / -gnu / ...). npm's
# optional-dependency platform resolution for these has a long-standing bug
# (npm/cli#4828) that reproduces reliably on Alpine/musl even though the
# musl variant is listed correctly in package-lock.json — `npm run build`
# fails with "Cannot find native binding" because no oxide binary actually
# lands in node_modules. Switching only this stage to a glibc base sidesteps
# musl detection entirely; confirmed locally (`docker compose build
# --no-cache frontend` fails identically with the same error on
# node:18-alpine). Same root cause breaks this stage in CI (e2e.yml and
# security-scan.yml's ZAP job both run `docker compose up -d ... frontend`
# on a fresh runner, forcing this exact build).
FROM node:20-bookworm-slim AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Also glibc, not Alpine: `npm ci --only=production` here independently
# resolves its own platform-specific optional deps, including
# @next/swc-linux-x64-*. On Alpine (musl) this hit the same npm bug as
# @tailwindcss/oxide above — confirmed locally: `npm ci --only=production`
# completed with no error, but node_modules ended up with NEITHER the gnu
# nor musl swc binary, so `next start`/`next dev` fell back to downloading
# both (~80MB combined) from npmjs.org at container startup. That's slow
# and unreliable even locally, and fatal in CI: e2e.yml's `wait-on
# http://localhost:3000 --timeout 60000` doesn't survive an 80MB runtime
# download on first boot. Matching the builder's glibc base makes the
# native binding land correctly at build time, same as above.
FROM node:20-bookworm-slim

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=https://api.production.com

COPY package*.json ./
RUN npm ci --only=production

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "start"]
