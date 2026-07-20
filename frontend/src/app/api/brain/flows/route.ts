/**
 * /api/brain/flows — flujos n8n self-contained (Vercel-safe).
 * Snapshot de las automatizaciones reales como flujos. Si el backend FastAPI
 * está vivo, el frontend prefiere /api/v1/brain/flows.
 */
import { NextResponse } from 'next/server'
import flows from '@/data/brain-flows.json'

export const runtime = 'nodejs'
export const revalidate = 3600

export async function GET(): Promise<NextResponse> {
  return NextResponse.json({ ...flows, source: 'bundled' })
}
