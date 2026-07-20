/**
 * /api/brain/activity — telemetría self-contained (Vercel-safe).
 *
 * Sin backend live no hay interacciones reales que reportar → idle (events vacío).
 * NUNCA inventa sinapsis. Cuando el backend FastAPI está arriba, NeuralGraphLive
 * usa /api/v1/brain/activity (bus real con eventos de agentes/tools/DB).
 */

import { NextResponse } from 'next/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(): Promise<NextResponse> {
  return NextResponse.json({
    events: [],
    stats: { total: 0, buffered: 0, by_kind: {}, last_ts: null },
    source: 'bundled-idle',
  })
}
