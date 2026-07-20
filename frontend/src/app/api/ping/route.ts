import { NextResponse } from 'next/server'

export const runtime = 'edge'

export const GET = (): NextResponse =>
  NextResponse.json({ ts: Date.now() }, { headers: { 'Cache-Control': 'no-store' } })
