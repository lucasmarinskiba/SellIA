'use client'

/**
 * SETTINGS DROPDOWN
 *
 * Botón de rueda con dropdown · controla theme + idioma globalmente.
 * Consume `useSettings()` desde `@/lib/settings`.
 */

import { useEffect, useRef, useState } from 'react'
import { Settings, Moon, Sun, Check, Globe } from 'lucide-react'
import { useSettings, LANG_META, type Theme, type Lang } from '@/lib/settings'

export default function SettingsDropdown(): React.JSX.Element {
  const { theme, lang, setTheme, setLang, t } = useSettings()
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)

  // Click outside close
  useEffect(() => {
    if (!open) return
    const onDown = (e: globalThis.MouseEvent): void => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  return (
    <div ref={wrapRef} style={{ position: 'relative', flexShrink: 0 }}>
      {/* Cog button */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        title={t('set.title')}
        aria-label={t('set.title')}
        aria-expanded={open}
        style={{
          width: 34, height: 34, borderRadius: 9,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: open ? 'rgba(59,130,246,0.12)' : 'rgba(255,255,255,0.04)',
          border: `1px solid ${open ? 'rgba(59,130,246,0.4)' : 'rgba(255,255,255,0.08)'}`,
          cursor: 'pointer',
          color: open ? '#3B82F6' : 'rgba(255,255,255,0.55)',
          flexShrink: 0,
          transition: 'background .15s, border-color .15s, color .15s, transform .25s',
        }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLButtonElement).style.transform = 'rotate(45deg)'
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLButtonElement).style.transform = 'rotate(0deg)'
        }}
      >
        <Settings size={15} />
      </button>

      {/* Dropdown */}
      {open && (
        <div style={{
          position: 'absolute', right: 0, top: 'calc(100% + 8px)',
          width: 280,
          background: 'rgba(8,10,18,0.98)',
          border: '1px solid rgba(255,255,255,0.14)',
          borderRadius: 14,
          overflow: 'hidden',
          zIndex: 300,
          boxShadow: '0 20px 60px rgba(0,0,0,.8)',
          backdropFilter: 'blur(20px)',
          fontFamily: "'Inter', ui-sans-serif, system-ui, sans-serif",
        }}>
          {/* Header */}
          <div style={{
            padding: '14px 16px',
            borderBottom: '1px solid rgba(255,255,255,0.07)',
            display: 'flex', alignItems: 'center', gap: 9,
          }}>
            <Settings size={14} style={{ color: '#3B82F6' }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: '#F0F4FF' }}>
              {t('set.title')}
            </span>
          </div>

          {/* Theme section */}
          <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{
              fontSize: 10, fontWeight: 700, fontFamily: 'monospace',
              letterSpacing: '0.08em', textTransform: 'uppercase',
              color: 'rgba(160,180,220,0.5)', marginBottom: 8,
            }}>
              {t('set.theme')}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {([
                { id: 'dark',  label: t('set.theme.dark'),  icon: <Moon size={13} /> },
                { id: 'light', label: t('set.theme.light'), icon: <Sun  size={13} /> },
              ] as { id: Theme; label: string; icon: React.JSX.Element }[]).map(opt => {
                const active = theme === opt.id
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setTheme(opt.id)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
                      padding: '9px 10px',
                      borderRadius: 8,
                      background: active ? 'rgba(59,130,246,0.14)' : 'transparent',
                      border: `1px solid ${active ? 'rgba(59,130,246,0.4)' : 'rgba(255,255,255,0.08)'}`,
                      color: active ? '#3B82F6' : 'rgba(200,210,240,0.7)',
                      cursor: 'pointer',
                      fontSize: 12, fontWeight: 600,
                      transition: 'background .15s, border-color .15s, color .15s',
                    }}
                    onMouseEnter={e => {
                      if (!active) {
                        const el = e.currentTarget as HTMLButtonElement
                        el.style.background = 'rgba(255,255,255,0.04)'
                        el.style.color = '#F0F4FF'
                      }
                    }}
                    onMouseLeave={e => {
                      if (!active) {
                        const el = e.currentTarget as HTMLButtonElement
                        el.style.background = 'transparent'
                        el.style.color = 'rgba(200,210,240,0.7)'
                      }
                    }}
                  >
                    {opt.icon}
                    {opt.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Language section */}
          <div style={{ padding: '12px 16px' }}>
            <div style={{
              fontSize: 10, fontWeight: 700, fontFamily: 'monospace',
              letterSpacing: '0.08em', textTransform: 'uppercase',
              color: 'rgba(160,180,220,0.5)', marginBottom: 8,
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <Globe size={11} /> {t('set.lang')}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {(Object.keys(LANG_META) as Lang[]).map(code => {
                const meta = LANG_META[code]
                const active = lang === code
                return (
                  <button
                    key={code}
                    type="button"
                    onClick={() => setLang(code)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '8px 10px',
                      borderRadius: 8,
                      background: active ? 'rgba(59,130,246,0.10)' : 'transparent',
                      border: `1px solid ${active ? 'rgba(59,130,246,0.30)' : 'transparent'}`,
                      color: active ? '#3B82F6' : 'rgba(200,210,240,0.75)',
                      cursor: 'pointer',
                      fontSize: 12, fontWeight: 500,
                      transition: 'background .15s, color .15s',
                      textAlign: 'left',
                    }}
                    onMouseEnter={e => {
                      if (!active) (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.04)'
                    }}
                    onMouseLeave={e => {
                      if (!active) (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                    }}
                  >
                    <span style={{ fontSize: 17, lineHeight: 1 }}>{meta.flag}</span>
                    <span style={{ flex: 1 }}>{meta.label}</span>
                    {active && <Check size={13} />}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Footer */}
          <div style={{
            padding: '10px 16px',
            borderTop: '1px solid rgba(255,255,255,0.07)',
            background: 'rgba(0,0,0,0.25)',
          }}>
            <p style={{
              margin: 0, fontSize: 10, fontFamily: 'monospace',
              color: 'rgba(160,180,220,0.4)', letterSpacing: '0.04em',
              lineHeight: 1.5,
            }}>
              Cambios aplicados globalmente · guardados en este dispositivo
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
