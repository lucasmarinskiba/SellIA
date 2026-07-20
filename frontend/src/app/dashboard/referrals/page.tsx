'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  Gift, Copy, Check, Users, DollarSign, TrendingUp, Loader2, Share2,
  MessageCircle, Mail, Trophy, Crown, ArrowUpRight,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

interface ReferralStats {
  has_code: boolean
  code?: string
  link?: string
  total_clicks: number
  total_signups: number
  total_conversions: number
  total_revenue_generated: number
  total_credits_earned: number
}

interface ConversionRecord {
  id: string
  date: string
  referred: string
  plan: string
  amount: number
  commission: number
}

interface LeaderboardEntry {
  rank: number
  name: string
  credits: number
  referrals: number
}

const mockMonthlyData = [
  { month: 'Ene', clicks: 45, signups: 12, conversions: 3 },
  { month: 'Feb', clicks: 62, signups: 18, conversions: 5 },
  { month: 'Mar', clicks: 58, signups: 15, conversions: 4 },
  { month: 'Abr', clicks: 85, signups: 28, conversions: 8 },
  { month: 'May', clicks: 110, signups: 35, conversions: 12 },
  { month: 'Jun', clicks: 95, signups: 30, conversions: 10 },
]

const mockConversions: ConversionRecord[] = [
  { id: '1', date: '2024-06-15', referred: 'María González', plan: 'Pro', amount: 49.99, commission: 10.00 },
  { id: '2', date: '2024-06-10', referred: 'Carlos Ruiz', plan: 'Business', amount: 99.99, commission: 20.00 },
  { id: '3', date: '2024-05-28', referred: 'Ana López', plan: 'Pro', amount: 49.99, commission: 10.00 },
  { id: '4', date: '2024-05-15', referred: 'Juan Pérez', plan: 'Starter', amount: 19.99, commission: 4.00 },
  { id: '5', date: '2024-05-02', referred: 'Lucía Martínez', plan: 'Pro', amount: 49.99, commission: 10.00 },
]

const mockLeaderboard: LeaderboardEntry[] = [
  { rank: 1, name: 'Alejandro S.', credits: 340, referrals: 28 },
  { rank: 2, name: 'Valentina R.', credits: 285, referrals: 24 },
  { rank: 3, name: 'Diego M.', credits: 210, referrals: 18 },
  { rank: 4, name: 'Camila F.', credits: 175, referrals: 15 },
  { rank: 5, name: 'Mateo L.', credits: 120, referrals: 10 },
]

const milestones = [0, 50, 100, 250, 500, 1000]

function getNextMilestone(current: number) {
  for (const m of milestones) {
    if (m > current) return m
  }
  return milestones[milestones.length - 1] * 2
}

function formatCurrency(value: number) {
  return `$${value.toFixed(2)}`
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function ReferralsPage() {
  const { user, loading: authLoading } = useAuth()
  const [stats, setStats] = useState<ReferralStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const res = await api.get('/referrals/stats')
      setStats(res.data)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  const copyCode = () => {
    if (stats?.code) {
      navigator.clipboard.writeText(stats.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const copyLink = () => {
    if (stats?.link) {
      navigator.clipboard.writeText(stats.link)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const shareWhatsApp = () => {
    if (!stats?.link) return
    const text = encodeURIComponent(`¡Usá mi código de referido y empezá a vender con IA! ${stats.link}`)
    window.open(`https://wa.me/?text=${text}`, '_blank')
  }

  const shareEmail = () => {
    if (!stats?.link) return
    const subject = encodeURIComponent('Te invito a probar SellIA')
    const body = encodeURIComponent(`Hola,\n\nTe invito a probar SellIA, la plataforma de ventas con IA.\n\nUsá mi link de referido: ${stats.link}\n\n¡Saludos!`)
    window.open(`mailto:?subject=${subject}&body=${body}`, '_blank')
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  const credits = stats?.total_credits_earned ?? 0
  const nextMilestone = getNextMilestone(credits)
  const progress = Math.min(100, (credits / nextMilestone) * 100)

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 rounded-xl bg-purple-500/10">
            <Gift className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Referidos</h1>
            <p className="text-sm text-white/50">Ganá créditos invitando amigos</p>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
          </div>
        ) : !stats?.has_code ? (
          <div className="text-center py-20 text-white/40">
            <p>No se encontró código de referido.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Code Card */}
            <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <h2 className="text-lg font-semibold text-white mb-4">Tu código de referido</h2>
              <div className="flex items-center gap-3 mb-4">
                <div className="flex-1 px-4 py-3 rounded-xl bg-white/[0.05] border border-white/[0.08] font-mono text-lg text-white text-center tracking-wider">
                  {stats.code}
                </div>
                <button
                  onClick={copyCode}
                  className="p-3 rounded-xl bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors"
                >
                  {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                </button>
              </div>
              <div className="flex items-center gap-3 mb-6">
                <div className="flex-1 px-4 py-3 rounded-xl bg-white/[0.05] border border-white/[0.08] text-sm text-white/60 truncate">
                  {stats.link}
                </div>
                <button
                  onClick={copyLink}
                  className="p-3 rounded-xl bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors"
                >
                  {copied ? <Check className="w-5 h-5" /> : <Share2 className="w-5 h-5" />}
                </button>
              </div>

              {/* Share Buttons */}
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={shareWhatsApp}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25 transition-colors text-sm font-medium"
                >
                  <MessageCircle className="w-4 h-4" />
                  WhatsApp
                </button>
                <button
                  onClick={shareEmail}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-500/15 text-blue-300 hover:bg-blue-500/25 transition-colors text-sm font-medium"
                >
                  <Mail className="w-4 h-4" />
                  Email
                </button>
                <button
                  onClick={copyLink}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/[0.06] text-white/70 hover:bg-white/[0.10] transition-colors text-sm font-medium"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copiado' : 'Copiar link'}
                </button>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                <div className="flex items-center gap-2 mb-2 text-purple-400">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-xs text-white/50">Clicks</span>
                </div>
                <p className="text-2xl font-bold text-white">{stats.total_clicks}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                <div className="flex items-center gap-2 mb-2 text-blue-400">
                  <Users className="w-4 h-4" />
                  <span className="text-xs text-white/50">Registros</span>
                </div>
                <p className="text-2xl font-bold text-white">{stats.total_signups}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                <div className="flex items-center gap-2 mb-2 text-emerald-400">
                  <Check className="w-4 h-4" />
                  <span className="text-xs text-white/50">Conversiones</span>
                </div>
                <p className="text-2xl font-bold text-white">{stats.total_conversions}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                <div className="flex items-center gap-2 mb-2 text-amber-400">
                  <DollarSign className="w-4 h-4" />
                  <span className="text-xs text-white/50">Créditos</span>
                </div>
                <p className="text-2xl font-bold text-white">${stats.total_credits_earned}</p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold text-white">Progreso hacia el siguiente hito</h2>
                <span className="text-sm text-white/50">
                  {formatCurrency(credits)} / {formatCurrency(nextMilestone)}
                </span>
              </div>
              <div className="w-full h-3 rounded-full bg-white/[0.06] overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-700"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="mt-3 text-sm text-white/50">
                Conseguí <span className="text-white font-medium">{formatCurrency(nextMilestone - credits)}</span> más para desbloquear el próximo hito.
              </p>
            </div>

            {/* AreaChart */}
            <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <h2 className="text-lg font-semibold text-white mb-6">Evolución mensual</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={mockMonthlyData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorClicks" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#A78BFA" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#A78BFA" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorSignups" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#60A5FA" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#60A5FA" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorConversions" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#34D399" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#34D399" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="month" stroke="rgba(255,255,255,0.3)" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }} />
                    <YAxis stroke="rgba(255,255,255,0.3)" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f1221',
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '12px',
                        color: '#fff',
                      }}
                      labelStyle={{ color: 'rgba(255,255,255,0.7)' }}
                    />
                    <Area type="monotone" dataKey="clicks" stroke="#A78BFA" fillOpacity={1} fill="url(#colorClicks)" strokeWidth={2} />
                    <Area type="monotone" dataKey="signups" stroke="#60A5FA" fillOpacity={1} fill="url(#colorSignups)" strokeWidth={2} />
                    <Area type="monotone" dataKey="conversions" stroke="#34D399" fillOpacity={1} fill="url(#colorConversions)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Conversion History Table */}
            <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <h2 className="text-lg font-semibold text-white mb-4">Historial de conversiones</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-white/[0.06]">
                      <th className="pb-3 text-xs font-medium text-white/40 uppercase tracking-wider">Fecha</th>
                      <th className="pb-3 text-xs font-medium text-white/40 uppercase tracking-wider">Referido</th>
                      <th className="pb-3 text-xs font-medium text-white/40 uppercase tracking-wider">Plan</th>
                      <th className="pb-3 text-xs font-medium text-white/40 uppercase tracking-wider text-right">Monto</th>
                      <th className="pb-3 text-xs font-medium text-white/40 uppercase tracking-wider text-right">Tu Comisión</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {mockConversions.map((c) => (
                      <tr key={c.id} className="group">
                        <td className="py-3.5 text-sm text-white/60">{formatDate(c.date)}</td>
                        <td className="py-3.5 text-sm text-white font-medium">{c.referred}</td>
                        <td className="py-3.5">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/70 border border-white/[0.06]">
                            {c.plan}
                          </span>
                        </td>
                        <td className="py-3.5 text-sm text-white/60 text-right">{formatCurrency(c.amount)}</td>
                        <td className="py-3.5 text-sm text-emerald-400 font-medium text-right">+{formatCurrency(c.commission)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Leaderboard */}
            <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <div className="flex items-center gap-2 mb-6">
                <Trophy className="w-5 h-5 text-amber-400" />
                <h2 className="text-lg font-semibold text-white">Top Referidores</h2>
              </div>
              <div className="space-y-3">
                {mockLeaderboard.map((entry) => (
                  <div
                    key={entry.rank}
                    className="flex items-center gap-4 p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] transition-colors"
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      entry.rank === 1
                        ? 'bg-amber-500/20 text-amber-300'
                        : entry.rank === 2
                        ? 'bg-slate-400/20 text-slate-300'
                        : entry.rank === 3
                        ? 'bg-orange-600/20 text-orange-300'
                        : 'bg-white/[0.05] text-white/50'
                    }`}>
                      {entry.rank <= 3 ? <Crown className="w-4 h-4" /> : entry.rank}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{entry.name}</p>
                      <p className="text-xs text-white/40">{entry.referrals} referidos</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-white">{formatCurrency(entry.credits)}</p>
                      <p className="text-xs text-white/40">créditos</p>
                    </div>
                    <ArrowUpRight className="w-4 h-4 text-white/20" />
                  </div>
                ))}
              </div>
            </div>

            {/* How it works */}
            <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <h2 className="text-lg font-semibold text-white mb-4">¿Cómo funciona?</h2>
              <div className="space-y-3">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-300 flex items-center justify-center text-sm font-bold">1</div>
                  <p className="text-sm text-white/70">Compartí tu código o link con amigos</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-300 flex items-center justify-center text-sm font-bold">2</div>
                  <p className="text-sm text-white/70">Ellos se registran y pagan su primer plan</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-300 flex items-center justify-center text-sm font-bold">3</div>
                  <p className="text-sm text-white/70">Ganás el 20% de su primera compra en créditos</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
