/**
 * /api/brain/cua/flows — sesiones Computer Use (Vercel-safe).
 * Sin backend live no hay sesiones → vacío. Con backend, el frontend usa
 * /api/v1/brain/cua/flows.
 */
import { NextResponse } from 'next/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(): Promise<NextResponse> {
  return NextResponse.json({ flows: [], source: 'bundled-idle' })
}
