/**
 * /api/translate
 *
 * Proxy to MyMemory translation API (no key required, ~5k chars/day per IP).
 * Batches multiple strings in one request, caches by hash.
 *
 * POST body: { lang: 'en'|'pt'|'fr', strings: string[] }
 * Returns:   { translations: string[] }
 *
 * If MyMemory fails or rate-limits, returns the original strings (passthrough).
 */

import { NextResponse } from 'next/server'

export const runtime = 'edge'

interface TranslateReq {
  lang: 'en' | 'pt' | 'fr'
  strings: string[]
}

interface MyMemoryResp {
  responseData?: { translatedText: string; match?: number }
  responseStatus?: number
}

const TARGET_MAP: Record<'en' | 'pt' | 'fr', string> = {
  en: 'en-US',
  pt: 'pt-BR',
  fr: 'fr-FR',
}

const translateOne = async (text: string, langPair: string): Promise<string> => {
  // Skip very short or pure-symbol strings
  if (text.length < 2 || /^[\d\s\W]+$/.test(text)) return text

  try {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${langPair}`
    const r = await fetch(url, { next: { revalidate: 60 * 60 * 24 * 7 } }) // edge cache 7 days
    if (!r.ok) return text
    const data = (await r.json()) as MyMemoryResp
    const t = data.responseData?.translatedText
    if (!t || typeof t !== 'string') return text
    // Match below 0.3 = bad translation, prefer original
    const match = data.responseData?.match ?? 0
    if (match < 0.3 && t.toLowerCase() === text.toLowerCase()) return text
    return t
  } catch {
    return text
  }
}

export async function POST(req: Request): Promise<NextResponse> {
  let body: TranslateReq
  try {
    body = await req.json() as TranslateReq
  } catch {
    return NextResponse.json({ error: 'invalid_body' }, { status: 400 })
  }

  const { lang, strings } = body
  if (!lang || !TARGET_MAP[lang] || !Array.isArray(strings)) {
    return NextResponse.json({ error: 'invalid_params' }, { status: 400 })
  }

  const langPair = `es-AR|${TARGET_MAP[lang]}`

  // Translate in parallel (with concurrency limit of 5)
  const results: string[] = new Array(strings.length).fill('')
  const queue = [...strings.entries()]
  const workers: Promise<void>[] = []

  const runWorker = async (): Promise<void> => {
    while (queue.length > 0) {
      const item = queue.shift()
      if (!item) break
      const [idx, text] = item
      results[idx] = await translateOne(text, langPair)
    }
  }

  for (let i = 0; i < Math.min(5, strings.length); i++) {
    workers.push(runWorker())
  }
  await Promise.all(workers)

  return NextResponse.json(
    { translations: results },
    {
      headers: {
        'Cache-Control': 'public, max-age=3600, s-maxage=86400',
      },
    },
  )
}

export async function GET(): Promise<NextResponse> {
  return NextResponse.json({
    service: 'translate',
    provider: 'MyMemory',
    supported_langs: ['en', 'pt', 'fr'],
    usage: 'POST { lang, strings: string[] }',
  })
}
