import { redirect } from 'next/navigation'

/**
 * There used to be two login screens (/login and this one) with the same backend call but different looks, and
 * session expiry bounced people between them. /login is the only one now; old links and bookmarks land there.
 */
export default async function SelliaLoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; from?: string }>
}) {
  const query = await searchParams
  const from = query.from ?? query.next
  redirect(from ? `/login?from=${encodeURIComponent(from)}` : '/login')
}
