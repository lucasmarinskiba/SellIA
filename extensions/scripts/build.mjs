#!/usr/bin/env node
/**
 * Cross-browser extension builder.
 *
 * Reads shared source from extensions/chrome/ + adapts manifest per target.
 * Outputs zip artifacts in extensions/dist/{chrome,edge,firefox}.
 *
 * Usage: node extensions/scripts/build.mjs [chrome|edge|firefox|all]
 */
import { execSync } from 'node:child_process'
import { copyFileSync, cpSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')
const DIST = join(ROOT, 'dist')
const CHROME_SRC = join(ROOT, 'chrome')

const SHARED_FILES = ['background.js', 'content.js', 'overlay.css', 'popup.html', 'popup.js', 'sidepanel.html', 'icons']

const TARGETS = {
  chrome: {
    manifestPatches: {},  // base
  },
  edge: {
    manifestPatches: {
      author: 'SellIA',
      browser_specific_settings: undefined,
    },
  },
  firefox: {
    manifestPatches: (m) => {
      // Firefox MV3 needs background.scripts (not service_worker) AND host_permissions in different shape.
      const out = { ...m }
      out.background = { scripts: ['background.js'] }
      out.browser_specific_settings = {
        gecko: { id: 'sellia@sellia.app', strict_min_version: '128.0' },
      }
      delete out.side_panel  // Firefox uses sidebar_action instead
      out.sidebar_action = {
        default_title: 'SellIA',
        default_panel: 'sidepanel.html',
        default_icon: { 16: 'icons/icon16.png', 48: 'icons/icon48.png' },
      }
      return out
    },
  },
}

function buildOne(target) {
  console.log(`\n→ Build ${target}`)
  const outDir = join(DIST, target)
  rmSync(outDir, { recursive: true, force: true })
  mkdirSync(outDir, { recursive: true })

  // Copy shared sources
  for (const f of SHARED_FILES) {
    const src = join(CHROME_SRC, f)
    if (!existsSync(src)) continue
    const dest = join(outDir, f)
    cpSync(src, dest, { recursive: true })
  }

  // Patch manifest
  const baseManifest = JSON.parse(readFileSync(join(CHROME_SRC, 'manifest.json'), 'utf-8'))
  const cfg = TARGETS[target]
  let manifest = baseManifest
  if (typeof cfg.manifestPatches === 'function') {
    manifest = cfg.manifestPatches(manifest)
  } else {
    manifest = { ...baseManifest, ...cfg.manifestPatches }
  }
  writeFileSync(join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2))

  // Zip
  const version = manifest.version
  const zipPath = join(DIST, `sellia-${target}-${version}.zip`)
  execSync(`cd ${outDir} && zip -qr ${zipPath} .`, { stdio: 'inherit' })
  console.log(`✓ ${target} → ${zipPath}`)
}

const arg = process.argv[2] || 'all'
const targets = arg === 'all' ? Object.keys(TARGETS) : [arg]

for (const t of targets) {
  if (!TARGETS[t]) {
    console.error(`✗ unknown target: ${t}`)
    process.exit(1)
  }
  buildOne(t)
}

console.log('\n✓ Done')
