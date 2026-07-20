/**
 * /api/brain/graph — grafo REAL del cerebro, self-contained (Vercel-safe).
 *
 * Snapshot del registry backend (agentes, skills, automatizaciones, conocimiento)
 * generado desde core/brain/registry.graph(). Garantiza que /sellia-brain muestre
 * el cerebro completo aunque el backend FastAPI (api.sellia.app) no esté arriba.
 * Cuando el backend live SÍ está, NeuralGraphLive prefiere /api/v1/brain/graph.
 */

import { NextResponse } from 'next/server'
import graph from '@/data/brain-graph.json'

export const runtime = 'nodejs'
export const revalidate = 3600

export async function GET(): Promise<NextResponse> {
  return NextResponse.json({
    ...graph,
    source: 'bundled-registry-snapshot',
    generated_at: new Date().toISOString(),
  })
}
