'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'
import {
  Brain, Zap, TrendingUp, Shield, Bot, MessageSquare, ArrowRight,
  Star, Check, ChevronDown, Sparkles, Globe2, Clock, BarChart3,
} from 'lucide-react'

/* ─── design tokens ─── */
const C = {
  bg:      '#0B0F19',
  panel:   'rgba(13,18,30,0.72)',
  cyan:    '#00D4FF',
  violet:  '#8B5CF6',
  emerald: '#10B981',
  lime:    '#d3ff3a',
  border:  'rgba(255,255,255,0.07)',
  muted:   'rgba(255,255,255,0.45)',
}

/* ═══════════════════════════════════════════════════════════
   3-D NEURAL BRAIN CANVAS
   Fibonacci sphere • 80 nodes • orthographic projection •
   mouse-parallax tilt • photon signals along edges
═══════════════════════════════════════════════════════════ */
const NeuralBrain3D = (): React.JSX.Element => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef  = useRef({ x: 0, y: 0 })
  const rafRef    = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const W = canvas.offsetWidth
    const H = canvas.offsetHeight
    canvas.width  = W * devicePixelRatio
    canvas.height = H * devicePixelRatio
    ctx.scale(devicePixelRatio, devicePixelRatio)

    /* ── fibonacci sphere nodes ── */
    const N  = 80
    const φ  = Math.PI * (3 - Math.sqrt(5))
    const R  = Math.min(W, H) * 0.38

    interface Node3D { ox: number; oy: number; oz: number; x: number; y: number; z: number; r: number; col: string }
    interface Edge   { a: number; b: number; photons: { t: number; speed: number }[] }

    const nodes: Node3D[] = Array.from({ length: N }, (_, i) => {
      const y  = 1 - (i / (N - 1)) * 2
      const r  = Math.sqrt(1 - y * y)
      const θ  = φ * i
      return { ox: Math.cos(θ) * r, oy: y, oz: Math.sin(θ) * r, x: 0, y: 0, z: 0, r: 0,
               col: i % 5 === 0 ? C.violet : i % 3 === 0 ? C.cyan : C.emerald }
    })

    /* connect nearby nodes */
    const MAX_DIST = 0.42
    const edges: Edge[] = []
    for (let a = 0; a < N; a++) {
      for (let b = a + 1; b < N; b++) {
        const dx = nodes[a].ox - nodes[b].ox
        const dy = nodes[a].oy - nodes[b].oy
        const dz = nodes[a].oz - nodes[b].oz
        if (Math.sqrt(dx*dx + dy*dy + dz*dz) < MAX_DIST) {
          edges.push({ a, b, photons: Math.random() < 0.25
            ? [{ t: Math.random(), speed: 0.003 + Math.random() * 0.004 }]
            : [] })
        }
      }
    }

    /* ── rotation state ── */
    let rotY = 0, rotX = 0.18

    const project = (n: Node3D, mx: number, my: number): void => {
      const rx = rotX + my * 0.3
      const ry = rotY + mx * 0.4
      /* rotate Y */
      const cosY = Math.cos(ry), sinY = Math.sin(ry)
      const x1 = n.ox * cosY + n.oz * sinY
      const z1 = -n.ox * sinY + n.oz * cosY
      /* rotate X */
      const cosX = Math.cos(rx), sinX = Math.sin(rx)
      const y2 = n.oy * cosX - z1 * sinX
      const z2 = n.oy * sinX + z1 * cosX
      const fov = 2.6
      const scale = fov / (fov + z2 + 1)
      n.x = W / 2 + x1 * R * scale
      n.y = H / 2 + y2 * R * scale
      n.z = z2
      n.r = Math.max(1.5, 4 * scale)
    }

    /* ── draw loop ── */
    const draw = (): void => {
      ctx.clearRect(0, 0, W, H)
      rotY += 0.004

      const mx = mouseRef.current.x
      const my = mouseRef.current.y

      nodes.forEach(n => project(n, mx, my))

      /* edges */
      edges.forEach(e => {
        const a = nodes[e.a], b = nodes[e.b]
        const vis = Math.max(0, (a.z + b.z) / 2 + 1.2)
        const alpha = Math.min(0.55, vis * 0.22)
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        /* cubic bezier for organic look */
        const cx1 = a.x + (b.x - a.x) * 0.35 + (a.y - b.y) * 0.18
        const cy1 = a.y + (b.y - a.y) * 0.35 - (a.x - b.x) * 0.1
        const cx2 = b.x - (b.x - a.x) * 0.35 + (a.y - b.y) * 0.1
        const cy2 = b.y - (b.y - a.y) * 0.35 - (a.x - b.x) * 0.08
        ctx.bezierCurveTo(cx1, cy1, cx2, cy2, b.x, b.y)
        ctx.strokeStyle = `rgba(0,212,255,${alpha})`
        ctx.lineWidth = 0.8
        ctx.stroke()

        /* photon signals */
        e.photons.forEach(p => {
          p.t += p.speed
          if (p.t > 1) p.t = 0
          const t = p.t
          const mt = 1 - t
          const px = mt*mt*mt*a.x + 3*mt*mt*t*cx1 + 3*mt*t*t*cx2 + t*t*t*b.x
          const py = mt*mt*mt*a.y + 3*mt*mt*t*cy1 + 3*mt*t*t*cy2 + t*t*t*b.y
          const g = ctx.createRadialGradient(px, py, 0, px, py, 5)
          g.addColorStop(0, 'rgba(0,212,255,0.9)')
          g.addColorStop(1, 'rgba(0,212,255,0)')
          ctx.beginPath()
          ctx.arc(px, py, 5, 0, Math.PI * 2)
          ctx.fillStyle = g
          ctx.fill()
        })
      })

      /* nodes */
      nodes.forEach(n => {
        const vis = Math.min(1, (n.z + 1.5) / 2.5)
        const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 2.5)
        g.addColorStop(0, n.col)
        g.addColorStop(0.4, n.col + '99')
        g.addColorStop(1, 'transparent')
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r * 2.5, 0, Math.PI * 2)
        ctx.fillStyle = g
        ctx.globalAlpha = vis * 0.85
        ctx.fill()
        ctx.globalAlpha = 1
        /* core dot */
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r * 0.7, 0, Math.PI * 2)
        ctx.fillStyle = '#ffffff'
        ctx.globalAlpha = vis * 0.9
        ctx.fill()
        ctx.globalAlpha = 1
      })

      rafRef.current = requestAnimationFrame(draw)
    }

    draw()

    const onMove = (e: MouseEvent): void => {
      const rect = canvas.getBoundingClientRect()
      mouseRef.current = {
        x: ((e.clientX - rect.left) / rect.width  - 0.5) * 2,
        y: ((e.clientY - rect.top)  / rect.height - 0.5) * 2,
      }
    }
    window.addEventListener('mousemove', onMove)
    return () => {
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener('mousemove', onMove)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', display: 'block' }}
    />
  )
}

/* ═══════════════════════════════════════════════════════════
   ANIMATED COUNTER
═══════════════════════════════════════════════════════════ */
const Counter = ({ to, suffix = '', prefix = '' }: { to: number; suffix?: string; prefix?: string }): React.JSX.Element => {
  const [val, setVal] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const obs = new IntersectionObserver(entries => {
      if (!entries[0].isIntersecting) return
      obs.disconnect()
      let start = 0
      const step = to / 60
      const t = setInterval(() => {
        start = Math.min(start + step, to)
        setVal(Math.round(start))
        if (start >= to) clearInterval(t)
      }, 16)
    })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [to])

  return <span ref={ref}>{prefix}{val.toLocaleString()}{suffix}</span>
}

/* ═══════════════════════════════════════════════════════════
   FAQ ITEM
═══════════════════════════════════════════════════════════ */
const FAQ = ({ q, a }: { q: string; a: string }): React.JSX.Element => {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ borderBottom: `1px solid ${C.border}` }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '20px 0', background: 'none', border: 'none', color: '#fff',
          fontSize: 16, fontWeight: 500, cursor: 'pointer', textAlign: 'left', gap: 16,
        }}
      >
        {q}
        <ChevronDown size={18} style={{ flexShrink: 0, transition: 'transform .2s', transform: open ? 'rotate(180deg)' : 'none', color: C.cyan }} />
      </button>
      {open && (
        <p style={{ margin: '0 0 20px', color: C.muted, fontSize: 15, lineHeight: 1.7 }}>{a}</p>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════════ */
export default function SelliaLanding(): React.JSX.Element {
  const [email, setEmail] = useState('')
  const [sent, setSent]   = useState(false)

  const handleSubmit = useCallback((e: React.FormEvent): void => {
    e.preventDefault()
    if (!email) return
    setSent(true)
  }, [email])

  return (
    <div style={{ background: C.bg, color: '#fff', fontFamily: "'Inter', 'Space Grotesk', sans-serif", minHeight: '100vh', overflowX: 'hidden' }}>

      {/* ── global styles ── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::selection { background: ${C.cyan}33; }
        ::-webkit-scrollbar { width: 6px; background: ${C.bg}; }
        ::-webkit-scrollbar-thumb { background: ${C.violet}66; border-radius: 3px; }
        .glow-cyan  { text-shadow: 0 0 40px ${C.cyan}99; }
        .glow-violet{ text-shadow: 0 0 40px ${C.violet}99; }
        .btn-primary {
          display: inline-flex; align-items: center; gap: 10px;
          background: linear-gradient(135deg, ${C.cyan}, ${C.violet});
          color: #0B0F19; font-weight: 700; font-size: 16px;
          padding: 14px 32px; border-radius: 12px; border: none; cursor: pointer;
          transition: transform .15s, box-shadow .15s;
          box-shadow: 0 0 32px ${C.cyan}55;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 0 48px ${C.cyan}88; }
        .btn-ghost {
          display: inline-flex; align-items: center; gap: 8px;
          background: transparent; border: 1px solid ${C.border}; color: #fff;
          font-size: 15px; padding: 12px 24px; border-radius: 10px; cursor: pointer;
          transition: border-color .15s, background .15s;
        }
        .btn-ghost:hover { border-color: ${C.cyan}88; background: ${C.cyan}11; }
        .glass-card {
          background: ${C.panel}; border: 1px solid ${C.border};
          backdrop-filter: blur(18px); border-radius: 16px;
        }
        @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }
        @keyframes pulse-ring {
          0% { transform: scale(0.85); opacity: 0.6; }
          50% { transform: scale(1.05); opacity: 0.2; }
          100% { transform: scale(0.85); opacity: 0.6; }
        }
        .float { animation: float 6s ease-in-out infinite; }
        .spin-ring { animation: pulse-ring 3s ease-in-out infinite; }
      `}</style>

      {/* ══════════════════════════════════════
          NAV
      ══════════════════════════════════════ */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '16px 40px', background: 'rgba(11,15,25,0.82)',
        backdropFilter: 'blur(20px)', borderBottom: `1px solid ${C.border}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: `linear-gradient(135deg, ${C.cyan}33, ${C.violet}33)`, border: `1px solid ${C.cyan}44`,
          }}>
            <Brain size={20} color={C.cyan} />
          </div>
          <span style={{ fontFamily: 'Space Grotesk', fontWeight: 700, fontSize: 20, letterSpacing: '-0.02em' }}>
            Sell<span style={{ color: C.cyan }}>IA</span>
          </span>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <Link href="/sellia-login" className="btn-ghost" style={{ fontSize: 14 }}>Iniciar sesión</Link>
          <Link href="/sellia-signup" className="btn-primary" style={{ fontSize: 14, padding: '10px 22px' }}>
            Empezar gratis
          </Link>
        </div>
      </nav>

      {/* ══════════════════════════════════════
          HERO
      ══════════════════════════════════════ */}
      <section style={{ position: 'relative', minHeight: '100vh', display: 'flex', alignItems: 'center', paddingTop: 80, overflow: 'hidden' }}>

        {/* ambient glow background */}
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          <div style={{ position: 'absolute', top: '20%', left: '50%', transform: 'translate(-50%,-50%)', width: 600, height: 600, borderRadius: '50%', background: `radial-gradient(circle, ${C.violet}22 0%, transparent 70%)` }} />
          <div style={{ position: 'absolute', top: '40%', right: '10%', width: 300, height: 300, borderRadius: '50%', background: `radial-gradient(circle, ${C.cyan}18 0%, transparent 70%)` }} />
          <div style={{ position: 'absolute', bottom: '10%', left: '15%', width: 250, height: 250, borderRadius: '50%', background: `radial-gradient(circle, ${C.emerald}15 0%, transparent 70%)` }} />
        </div>

        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 40px', width: '100%', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'center' }}>

          {/* left — copy */}
          <div>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 16px',
              background: `${C.cyan}18`, border: `1px solid ${C.cyan}44`, borderRadius: 100,
              fontSize: 13, color: C.cyan, fontWeight: 600, marginBottom: 28,
            }}>
              <Sparkles size={14} /> Inteligencia Artificial de Ventas · Generación 4
            </div>

            <h1 className="glow-violet" style={{
              fontFamily: 'Space Grotesk', fontSize: 'clamp(40px, 5vw, 68px)',
              fontWeight: 700, lineHeight: 1.08, letterSpacing: '-0.03em', marginBottom: 24,
            }}>
              El cerebro que<br />
              <span style={{ background: `linear-gradient(90deg, ${C.cyan}, ${C.violet})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                vende por vos
              </span><br />
              24 / 7
            </h1>

            <p style={{ fontSize: 18, color: C.muted, lineHeight: 1.7, marginBottom: 36, maxWidth: 480 }}>
              SellIA es un agente de ventas autónomo impulsado por IA que califica, persuade y cierra negocios mientras dormís. Integralo en minutos.
            </p>

            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 48 }}>
              <Link href="/sellia-signup" className="btn-primary">
                Activar mi agente <ArrowRight size={18} />
              </Link>
              <Link href="/sellia-brain" className="btn-ghost">
                Ver demo en vivo
              </Link>
            </div>

            <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
              {[
                { icon: <Check size={14} />, text: 'Sin tarjeta de crédito' },
                { icon: <Check size={14} />, text: '14 días gratis' },
                { icon: <Check size={14} />, text: 'Setup en 5 minutos' },
              ].map(({ icon, text }) => (
                <div key={text} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 14, color: C.muted }}>
                  <span style={{ color: C.emerald }}>{icon}</span> {text}
                </div>
              ))}
            </div>
          </div>

          {/* right — 3D brain canvas */}
          <div className="float" style={{ position: 'relative', height: 520 }}>
            {/* outer ring */}
            <div className="spin-ring" style={{
              position: 'absolute', inset: -20, borderRadius: '50%',
              border: `1px solid ${C.cyan}33`, pointerEvents: 'none',
            }} />
            <div style={{
              position: 'absolute', inset: -60, borderRadius: '50%',
              border: `1px dashed ${C.violet}22`, pointerEvents: 'none',
            }} />
            {/* canvas */}
            <div style={{
              position: 'relative', height: '100%', borderRadius: 24,
              background: `radial-gradient(ellipse at center, ${C.violet}15 0%, transparent 70%)`,
              overflow: 'hidden',
            }}>
              <NeuralBrain3D />
              {/* HUD overlays on canvas */}
              <div style={{ position: 'absolute', top: 20, left: 20, padding: '8px 14px', background: C.panel, border: `1px solid ${C.cyan}44`, borderRadius: 10, fontSize: 12, color: C.cyan, backdropFilter: 'blur(10px)' }}>
                <span style={{ opacity: 0.6 }}>NEURAL SYNC</span>
                <br />
                <span style={{ fontFamily: 'monospace', fontSize: 15 }}>98.4%</span>
              </div>
              <div style={{ position: 'absolute', top: 20, right: 20, padding: '8px 14px', background: C.panel, border: `1px solid ${C.violet}44`, borderRadius: 10, fontSize: 12, color: C.violet, backdropFilter: 'blur(10px)' }}>
                <span style={{ opacity: 0.6 }}>LEADS ACTIVOS</span>
                <br />
                <span style={{ fontFamily: 'monospace', fontSize: 15 }}>2,847</span>
              </div>
              <div style={{ position: 'absolute', bottom: 20, left: 20, right: 20, padding: '10px 16px', background: C.panel, border: `1px solid ${C.emerald}44`, borderRadius: 10, fontSize: 12, backdropFilter: 'blur(10px)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: C.emerald }}>● AGENTE EN LÍNEA</span>
                <span style={{ color: C.muted, fontFamily: 'monospace' }}>12 conv. activas</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          SOCIAL PROOF STRIP
      ══════════════════════════════════════ */}
      <section style={{ padding: '40px 40px', borderTop: `1px solid ${C.border}`, borderBottom: `1px solid ${C.border}` }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <p style={{ textAlign: 'center', fontSize: 13, color: C.muted, marginBottom: 24, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            Confían en SellIA
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 48, flexWrap: 'wrap', alignItems: 'center' }}>
            {['Mercado Libre', 'Tienda Nube', 'Shopify', 'WooCommerce', 'HubSpot', 'Zoho CRM'].map(brand => (
              <span key={brand} style={{ fontSize: 15, fontWeight: 600, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.05em' }}>{brand}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          STATS
      ══════════════════════════════════════ */}
      <section style={{ padding: '80px 40px' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
          {[
            { n: 12400,  s: '+',   label: 'Ventas cerradas',       col: C.cyan    },
            { n: 98,     s: '%',   label: 'Tasa de respuesta',      col: C.violet  },
            { n: 4700,   s: '%',   label: 'ROI promedio',           col: C.emerald },
            { n: 5,      s: 'min', label: 'Setup inicial',          col: C.lime    },
          ].map(({ n, s, label, col }) => (
            <div key={label} className="glass-card" style={{ padding: '32px 28px', textAlign: 'center', borderRadius: 0 }}>
              <div style={{ fontFamily: 'Space Grotesk', fontSize: 48, fontWeight: 700, color: col, lineHeight: 1, marginBottom: 8 }}>
                <Counter to={n} suffix={s} />
              </div>
              <div style={{ fontSize: 14, color: C.muted }}>{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ══════════════════════════════════════
          HOW IT WORKS (3-step)
      ══════════════════════════════════════ */}
      <section style={{ padding: '80px 40px', background: 'rgba(255,255,255,0.015)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 64 }}>
            <h2 style={{ fontFamily: 'Space Grotesk', fontSize: 'clamp(28px, 4vw, 48px)', fontWeight: 700, marginBottom: 16 }}>
              Activá el cerebro en <span style={{ color: C.cyan }}>3 pasos</span>
            </h2>
            <p style={{ color: C.muted, fontSize: 17, maxWidth: 520, margin: '0 auto' }}>Sin código. Sin configuraciones complicadas. Tu agente opera desde el minuto uno.</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24 }}>
            {[
              { step: '01', icon: <Globe2 size={28} />, title: 'Conectá tu canal', desc: 'WhatsApp, Instagram, email, web chat. SellIA absorbe el contexto de tu negocio en minutos.', col: C.cyan },
              { step: '02', icon: <Brain size={28} />, title: 'El cerebro aprende', desc: 'Carga tu catálogo, objeciones y scripts. El modelo se entrena con tu voz de marca.', col: C.violet },
              { step: '03', icon: <TrendingUp size={28} />, title: 'Cerrá ventas solo', desc: 'SellIA califica, persuade y convierte. Vos supervisás. Él ejecuta.', col: C.emerald },
            ].map(({ step, icon, title, desc, col }) => (
              <div key={step} className="glass-card" style={{ padding: 32, position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: 16, right: 20, fontFamily: 'Space Grotesk', fontSize: 64, fontWeight: 800, color: `${col}12`, lineHeight: 1 }}>{step}</div>
                <div style={{ color: col, marginBottom: 20 }}>{icon}</div>
                <h3 style={{ fontFamily: 'Space Grotesk', fontSize: 22, fontWeight: 700, marginBottom: 12 }}>{title}</h3>
                <p style={{ color: C.muted, fontSize: 15, lineHeight: 1.7 }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          FEATURES GRID
      ══════════════════════════════════════ */}
      <section style={{ padding: '80px 40px' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 64 }}>
            <h2 style={{ fontFamily: 'Space Grotesk', fontSize: 'clamp(28px, 4vw, 48px)', fontWeight: 700, marginBottom: 16 }}>
              Todo lo que tu vendedor ideal<br /><span style={{ color: C.violet }}>nunca olvida</span>
            </h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
            {[
              { icon: <Bot size={24} />, col: C.cyan, title: 'Agente Autónomo 24/7', desc: 'Responde leads en segundos, califica, negocia y cierra sin intervención humana.' },
              { icon: <MessageSquare size={24} />, col: C.violet, title: 'Omnicanal nativo', desc: 'WhatsApp Business API, IG DMs, email, web chat y más — una sola bandeja.' },
              { icon: <BarChart3 size={24} />, col: C.emerald, title: 'Pipeline en tiempo real', desc: 'Visualizá el embudo de ventas con métricas vivas. KPIs que importan.' },
              { icon: <Shield size={24} />, col: C.lime, title: 'Modo supervisado', desc: 'Aprobás cada acción antes de ejecutar. Control total cuando lo necesitás.' },
              { icon: <Zap size={24} />, col: C.cyan, title: 'Respuesta en < 2 segundos', desc: 'Latencia ultra baja. El lead nunca espera. Ningún momento de interés se pierde.' },
              { icon: <Clock size={24} />, col: C.violet, title: 'Memoria persistente', desc: 'SellIA recuerda cada interacción, preferencia y objeción de cada lead.' },
            ].map(({ icon, col, title, desc }) => (
              <div key={title} className="glass-card" style={{ padding: 28, transition: 'border-color .2s', cursor: 'default' }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = col + '66')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = C.border)}
              >
                <div style={{ color: col, marginBottom: 16, padding: 10, background: col + '18', borderRadius: 10, display: 'inline-flex' }}>{icon}</div>
                <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 10 }}>{title}</h3>
                <p style={{ color: C.muted, fontSize: 14, lineHeight: 1.7 }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          TESTIMONIALS
      ══════════════════════════════════════ */}
      <section style={{ padding: '80px 40px', background: 'rgba(255,255,255,0.015)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <h2 style={{ fontFamily: 'Space Grotesk', textAlign: 'center', fontSize: 'clamp(24px, 3vw, 40px)', fontWeight: 700, marginBottom: 48 }}>
            Lo que dicen los que ya lo usan
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
            {[
              { name: 'Martín Villanueva', role: 'CEO · Indumentaria digital', text: 'SellIA triplicó mi conversión en 3 semanas. Ahora duermo y cuando me levanto hay órdenes nuevas.', stars: 5 },
              { name: 'Carolina Reyes', role: 'Fundadora · Clínica estética', text: 'Lo conecté a Instagram y WhatsApp. Agenda citas, responde consultas y filtra los leads calificados.', stars: 5 },
              { name: 'Diego Ferreira', role: 'Dir. Comercial · SaaS B2B', text: 'En demos enterprises cerramos 40% más rápido. El agente hace el calentamiento antes de que yo entre.', stars: 5 },
            ].map(({ name, role, text, stars }) => (
              <div key={name} className="glass-card" style={{ padding: 28 }}>
                <div style={{ display: 'flex', gap: 2, marginBottom: 16 }}>
                  {Array(stars).fill(0).map((_, i) => <Star key={i} size={14} fill={C.lime} color={C.lime} />)}
                </div>
                <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 15, lineHeight: 1.7, marginBottom: 20 }}>"{text}"</p>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{name}</div>
                  <div style={{ fontSize: 12, color: C.muted }}>{role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          PRICING
      ══════════════════════════════════════ */}
      <section style={{ padding: '80px 40px' }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{ fontFamily: 'Space Grotesk', textAlign: 'center', fontSize: 'clamp(24px, 3vw, 40px)', fontWeight: 700, marginBottom: 12 }}>
            Precios simples
          </h2>
          <p style={{ textAlign: 'center', color: C.muted, marginBottom: 48 }}>Sin costos ocultos. Cancelá cuando quieras.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20 }}>
            {[
              {
                name: 'Starter', price: '$49', per: '/mes', col: C.cyan, popular: false,
                features: ['1 canal conectado', '500 conversaciones/mes', 'Pipeline básico', 'Soporte por email'],
              },
              {
                name: 'Growth', price: '$149', per: '/mes', col: C.violet, popular: true,
                features: ['5 canales conectados', '5.000 conversaciones/mes', 'Full HUD dashboard', 'Computer Use supervisado', 'Soporte prioritario'],
              },
              {
                name: 'Agency', price: '$399', per: '/mes', col: C.emerald, popular: false,
                features: ['Canales ilimitados', 'Conversaciones ilimitadas', 'Multi-tenant', 'Piloto automático 24/7', 'SLA garantizado'],
              },
            ].map(({ name, price, per, col, popular, features }) => (
              <div key={name} className="glass-card" style={{ padding: 32, position: 'relative', borderColor: popular ? col + '66' : C.border, boxShadow: popular ? `0 0 40px ${col}22` : 'none' }}>
                {popular && (
                  <div style={{ position: 'absolute', top: -14, left: '50%', transform: 'translateX(-50%)', background: `linear-gradient(90deg, ${C.cyan}, ${C.violet})`, color: '#0B0F19', fontSize: 12, fontWeight: 700, padding: '4px 16px', borderRadius: 100, whiteSpace: 'nowrap' }}>
                    MÁS POPULAR
                  </div>
                )}
                <h3 style={{ fontFamily: 'Space Grotesk', fontSize: 20, fontWeight: 700, marginBottom: 8, color: col }}>{name}</h3>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 24 }}>
                  <span style={{ fontFamily: 'Space Grotesk', fontSize: 40, fontWeight: 800 }}>{price}</span>
                  <span style={{ color: C.muted, fontSize: 14 }}>{per}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 28 }}>
                  {features.map(f => (
                    <div key={f} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', fontSize: 14 }}>
                      <Check size={14} style={{ color: col, flexShrink: 0, marginTop: 2 }} /> {f}
                    </div>
                  ))}
                </div>
                <Link href="/sellia-signup" className="btn-primary" style={{ width: '100%', justifyContent: 'center', background: popular ? `linear-gradient(135deg, ${C.cyan}, ${C.violet})` : `${col}22`, color: popular ? '#0B0F19' : col, boxShadow: 'none' }}>
                  Empezar
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════
          FAQ
      ══════════════════════════════════════ */}
      <section style={{ padding: '80px 40px', background: 'rgba(255,255,255,0.015)' }}>
        <div style={{ maxWidth: 720, margin: '0 auto' }}>
          <h2 style={{ fontFamily: 'Space Grotesk', textAlign: 'center', fontSize: 'clamp(24px, 3vw, 40px)', fontWeight: 700, marginBottom: 48 }}>
            Preguntas frecuentes
          </h2>
          {[
            { q: '¿SellIA reemplaza a mi equipo de ventas?', a: 'No lo reemplaza — lo multiplica. SellIA maneja el volumen de conversaciones repetitivas y qualificación, liberando a tu equipo para cerrar los deals de alto valor que requieren toque humano.' },
            { q: '¿Cuánto tiempo lleva la configuración?', a: 'La mayoría de los usuarios activan el agente en menos de 5 minutos. Conectás tu canal, cargás tu catálogo o link de tu web y el cerebro aprende solo.' },
            { q: '¿Funciona con WhatsApp Business?', a: 'Sí. SellIA se integra directamente con la API oficial de WhatsApp Business. También soporta Instagram DMs, email, web chat, Telegram y más.' },
            { q: '¿Puedo controlar lo que dice el agente?', a: 'Totalmente. En modo Supervisado aprobás cada mensaje antes de enviarse. En modo Piloto Automático el agente opera solo, pero podés interrumpirlo en cualquier momento.' },
            { q: '¿Hay contrato de permanencia?', a: 'No. Todos los planes son mensuales y podés cancelar cuando quieras desde tu panel sin penalizaciones.' },
          ].map(faq => <FAQ key={faq.q} q={faq.q} a={faq.a} />)}
        </div>
      </section>

      {/* ══════════════════════════════════════
          FINAL CTA
      ══════════════════════════════════════ */}
      <section style={{ padding: '100px 40px', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse at 50% 50%, ${C.violet}25 0%, transparent 70%)`, pointerEvents: 'none' }} />
        <div style={{ maxWidth: 640, margin: '0 auto', textAlign: 'center', position: 'relative' }}>
          <Brain size={56} color={C.cyan} style={{ margin: '0 auto 24px', display: 'block' }} />
          <h2 className="glow-cyan" style={{ fontFamily: 'Space Grotesk', fontSize: 'clamp(28px, 4vw, 52px)', fontWeight: 700, lineHeight: 1.1, marginBottom: 20 }}>
            Tu agente de ventas<br />
            <span style={{ color: C.cyan }}>está listo para activar</span>
          </h2>
          <p style={{ color: C.muted, fontSize: 17, marginBottom: 40, lineHeight: 1.7 }}>
            Empezá gratis. Sin tarjeta. 14 días para probar todo el poder del cerebro digital.
          </p>
          {!sent ? (
            <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 12, maxWidth: 440, margin: '0 auto', flexWrap: 'wrap', justifyContent: 'center' }}>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="tu@email.com"
                required
                style={{
                  flex: 1, minWidth: 200, padding: '14px 20px', borderRadius: 12, border: `1px solid ${C.border}`,
                  background: 'rgba(255,255,255,0.05)', color: '#fff', fontSize: 16, outline: 'none',
                }}
              />
              <button type="submit" className="btn-primary" style={{ whiteSpace: 'nowrap' }}>
                Activar gratis <ArrowRight size={16} />
              </button>
            </form>
          ) : (
            <div style={{ padding: '20px 32px', background: `${C.emerald}22`, border: `1px solid ${C.emerald}55`, borderRadius: 14, color: C.emerald, fontSize: 16, fontWeight: 600 }}>
              ✓ Perfecto. Te contactamos en las próximas horas.
            </div>
          )}
        </div>
      </section>

      {/* ══════════════════════════════════════
          FOOTER
      ══════════════════════════════════════ */}
      <footer style={{ padding: '40px', borderTop: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Brain size={18} color={C.cyan} />
          <span style={{ fontFamily: 'Space Grotesk', fontWeight: 700 }}>Sell<span style={{ color: C.cyan }}>IA</span></span>
        </div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          {['Privacidad', 'Términos', 'Seguridad', 'API Docs'].map(l => (
            <span key={l} style={{ fontSize: 13, color: C.muted, cursor: 'pointer' }}>{l}</span>
          ))}
        </div>
        <p style={{ fontSize: 13, color: C.muted }}>© 2026 SellIA · Somos Paithon Labs</p>
      </footer>

    </div>
  )
}
