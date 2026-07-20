#!/usr/bin/env node
/**
 * gen:brain — regenera el snapshot REAL del grafo del cerebro.
 *
 * Corre el registry de Python (core/brain/registry.graph()) y escribe
 * src/data/brain-graph.json (nodos+edges reales: agentes, skills, automatizaciones,
 * plataformas). Lo usa NeuralGraphLive como fallback Vercel-safe.
 *
 * Es BEST-EFFORT y NUNCA falla el build:
 *   - dev local (con Python + backend) → regenera el snapshot al día.
 *   - Vercel (sin Python ni backend) → conserva el snapshot ya commiteado.
 * En ambos casos exit 0.
 */

import { execFileSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const frontend = resolve(here, '..')
const backend = resolve(frontend, '..', 'backend')
const out = resolve(frontend, 'src', 'data', 'brain-graph.json')

const PY = [
  'import json,os',
  'from app.core.brain import get_brain_registry',
  'r=get_brain_registry()',
  'g=r.graph()',
  "out=os.environ['BRAIN_OUT']",
  'os.makedirs(os.path.dirname(out),exist_ok=True)',
  "json.dump({'nodes':g['nodes'],'edges':g['edges'],'counts':g['counts'],'health':g['health']},open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=0)",
  "fout=os.path.join(os.path.dirname(out),'brain-flows.json')",
  "json.dump(r.flows(),open(fout,'w',encoding='utf-8'),ensure_ascii=False,indent=0)",
  "print('[gen:brain] nodos',len(g['nodes']),'edges',len(g['edges']),'flows',len(r.flows()['flows']))",
].join('\n')

if (!existsSync(backend)) {
  console.log('[gen:brain] backend no presente en este build — uso snapshot commiteado')
  process.exit(0)
}

const candidates = process.platform === 'win32' ? ['py', 'python', 'python3'] : ['python3', 'python']
for (const cmd of candidates) {
  try {
    const o = execFileSync(cmd, ['-c', PY], {
      cwd: backend,
      env: { ...process.env, BRAIN_OUT: out },
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    console.log(o.toString().trim())
    process.exit(0)
  } catch {
    /* probar siguiente intérprete */
  }
}

console.log('[gen:brain] Python no disponible — uso snapshot commiteado (build OK)')
process.exit(0)
