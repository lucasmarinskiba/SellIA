'use client'

import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { businessApi } from '@/lib/business'
import {
  leaderboardApi,
  LeaderboardEntry,
  UserRank,
  NearbyUsers,
  TeamStats,
  LeaderboardMetric,
  METRIC_LABELS,
} from '@/lib/api/leaderboard'
import {
  Trophy,
  Medal,
  Crown,
  Flame,
  TrendingUp,
  Users,
  Star,
  Zap,
  Target,
  ArrowUp,
  Sparkles,
  ChevronRight,
} from 'lucide-react'

/* ============================================================
   LEADERBOARD PAGE — Social, Competitive, Supportive
   ============================================================ */

const METRICS: LeaderboardMetric[] = [
  'total_xp',
  'total_sales_closed',
  'total_revenue_generated',
  'total_referrals_generated',
  'current_login_streak',
  'total_achievements',
]

const METRIC_ICONS: Record<LeaderboardMetric, React.ElementType> = {
  total_xp: Zap,
  total_sales_closed: Target,
  total_revenue_generated: TrendingUp,
  total_referrals_generated: Users,
  current_login_streak: Flame,
  total_achievements: Star,
}

function formatMetricValue(metric: LeaderboardMetric, value: number): string {
  if (metric === 'total_revenue_generated') {
    return `$${value.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  }
  return value.toLocaleString('es-AR')
}

/* ---------- Podium Card ---------- */
function PodiumCard({
  entry,
  place,
  metric,
}: {
  entry: LeaderboardEntry
  place: number
  metric: LeaderboardMetric
}) {
  const isFirst = place === 1
  const isSecond = place === 2

  const gradient = isFirst
    ? 'from-yellow-400/20 via-yellow-500/10 to-transparent'
    : isSecond
    ? 'from-slate-300/20 via-slate-400/10 to-transparent'
    : 'from-amber-600/20 via-amber-700/10 to-transparent'

  const borderColor = isFirst
    ? 'border-yellow-400/30'
    : isSecond
    ? 'border-slate-300/20'
    : 'border-amber-600/30'

  const textColor = isFirst
    ? 'text-yellow-400'
    : isSecond
    ? 'text-slate-300'
    : 'text-amber-500'

  const crownSize = isFirst ? 'w-8 h-8' : 'w-6 h-6'
  const heightClass = isFirst ? 'h-56' : 'h-44'

  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: place * 0.1, type: 'spring', stiffness: 120 }}
      className={`relative flex flex-col items-center justify-end rounded-2xl border ${borderColor} ${heightClass} p-5 overflow-hidden`}
    >
      <div className={`absolute inset-0 bg-gradient-to-b ${gradient}`} />
      {isFirst && (
        <motion.div
          className="absolute top-4"
          animate={{ scale: [1, 1.15, 1] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          <Crown className={`${crownSize} ${textColor} drop-shadow-lg`} />
        </motion.div>
      )}
      <div className="relative z-10 flex flex-col items-center gap-2">
        <div
          className={`w-14 h-14 rounded-full flex items-center justify-center text-lg font-bold border-2 ${borderColor} ${textColor} bg-[#0a0e1a]`}
        >
          {place}
        </div>
        <p className="text-white font-semibold text-sm text-center leading-tight">
          {entry.full_name}
        </p>
        <p className={`text-xs font-bold ${textColor}`}>
          {formatMetricValue(metric, entry[metric] as number)}
        </p>
        <div className="flex items-center gap-1 text-[10px] text-white/40">
          <Star className="w-3 h-3" />
          Nivel {entry.level}
        </div>
      </div>
    </motion.div>
  )
}

/* ---------- Nearby Card ---------- */
function NearbyCard({
  entry,
  metric,
  currentUserId,
}: {
  entry: LeaderboardEntry
  metric: LeaderboardMetric
  currentUserId?: string
}) {
  const isMe = entry.user_id === currentUserId

  return (
    <motion.div
      whileHover={{ scale: 1.03 }}
      className={`flex items-center gap-3 rounded-xl px-4 py-3 border ${
        isMe
          ? 'bg-brand-orange/10 border-brand-orange/30'
          : 'bg-white/[0.02] border-white/[0.06]'
      }`}
    >
      <span
        className={`text-sm font-bold w-6 text-center ${
          entry.rank <= 3 ? 'text-yellow-400' : 'text-white/40'
        }`}
      >
        #{entry.rank}
      </span>
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium truncate ${isMe ? 'text-brand-orange' : 'text-white'}`}>
          {entry.full_name} {isMe && '(Vos)'}
        </p>
        <p className="text-xs text-white/40">Nivel {entry.level}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-bold text-white">
          {formatMetricValue(metric, entry[metric] as number)}
        </p>
      </div>
    </motion.div>
  )
}

/* ---------- Main Page ---------- */
export default function LeaderboardPage() {
  const { user } = useAuth()
  const [businessId, setBusinessId] = useState<string>('')
  const [metric, setMetric] = useState<LeaderboardMetric>('total_xp')
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [myRank, setMyRank] = useState<UserRank | null>(null)
  const [nearby, setNearby] = useState<NearbyUsers | null>(null)
  const [teamStats, setTeamStats] = useState<TeamStats | null>(null)
  const [loading, setLoading] = useState(true)

  // Fetch business id on mount
  useEffect(() => {
    businessApi.list().then((bizs) => {
      if (bizs.length > 0) setBusinessId(bizs[0].id)
    })
  }, [])

  // Fetch all leaderboard data
  useEffect(() => {
    if (!businessId) return
    setLoading(true)
    Promise.all([
      leaderboardApi.getLeaderboard(businessId, metric),
      leaderboardApi.getMyRank(businessId, metric),
      leaderboardApi.getNearby(businessId, metric),
      leaderboardApi.getTeamStats(businessId),
    ])
      .then(([lb, rank, near, stats]) => {
        setLeaderboard(lb)
        setMyRank(rank)
        setNearby(near)
        setTeamStats(stats)
      })
      .catch(() => {
        // Silencioso: dejamos estados vacíos
      })
      .finally(() => setLoading(false))
  }, [businessId, metric])

  const topThree = useMemo(() => leaderboard.slice(0, 3), [leaderboard])
  const rest = useMemo(() => leaderboard.slice(3), [leaderboard])

  const currentUserId = user?.id

  // Compute "A X de superar" message
  const overtakeMsg = useMemo(() => {
    if (!nearby || !myRank || myRank.rank === null || myRank.rank <= 1) return null
    const above = nearby.nearby.find((e) => e.rank === (myRank.rank! - 1))
    if (!above) return null
    const myEntry = nearby.nearby.find((e) => e.user_id === currentUserId)
    if (!myEntry) return null
    const diff = (above[metric] as number) - (myEntry[metric] as number)
    if (diff <= 0) return null
    return `¡A ${formatMetricValue(metric, Math.ceil(diff))} de superar a ${above.full_name}!`
  }, [nearby, myRank, metric, currentUserId])

  if (!businessId && !loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <div className="text-center">
          <Trophy className="w-12 h-12 text-white/20 mx-auto mb-4" />
          <p className="text-white/60">No tenés negocios cargados todavía.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060812] text-white pb-20">
      {/* Header / Team Stats */}
      <div className="border-b border-white/[0.06] bg-[#060812]/80 backdrop-blur-xl sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
              <Trophy className="w-5 h-5 text-brand-orange" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Ranking del Equipo</h1>
              <p className="text-xs text-white/40">Estamos en esto juntos 💪</p>
            </div>
          </div>

          {teamStats && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-3"
            >
              <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-4">
                <div className="flex items-center gap-2 text-white/40 mb-1">
                  <Users className="w-4 h-4" />
                  <span className="text-xs font-medium">Miembros</span>
                </div>
                <p className="text-xl font-bold text-white">{teamStats.total_members}</p>
              </div>
              <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-4">
                <div className="flex items-center gap-2 text-white/40 mb-1">
                  <Target className="w-4 h-4" />
                  <span className="text-xs font-medium">Ventas</span>
                </div>
                <p className="text-xl font-bold text-white">{teamStats.total_sales}</p>
              </div>
              <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-4">
                <div className="flex items-center gap-2 text-white/40 mb-1">
                  <Flame className="w-4 h-4" />
                  <span className="text-xs font-medium">Racha promedio</span>
                </div>
                <p className="text-xl font-bold text-white">{teamStats.avg_streak} días</p>
              </div>
              <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-4">
                <div className="flex items-center gap-2 text-white/40 mb-1">
                  <Sparkles className="w-4 h-4" />
                  <span className="text-xs font-medium">Top</span>
                </div>
                <p className="text-sm font-bold text-white truncate">
                  {teamStats.top_performer_name || '—'}
                </p>
                <p className="text-[10px] text-white/40">{teamStats.top_performer_xp} XP</p>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 pt-6 space-y-8">
        {/* Metric Selector */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1">
          {METRICS.map((m) => {
            const Icon = METRIC_ICONS[m]
            const active = m === metric
            return (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all border ${
                  active
                    ? 'bg-brand-orange/10 text-brand-orange border-brand-orange/30'
                    : 'bg-white/[0.02] text-white/50 border-transparent hover:bg-white/[0.04] hover:text-white/70'
                }`}
              >
                <Icon className="w-4 h-4" />
                {METRIC_LABELS[m]}
              </button>
            )
          })}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center animate-pulse">
                <Trophy className="w-5 h-5 text-brand-orange" />
              </div>
              <p className="text-sm text-white/40">Cargando ranking...</p>
            </div>
          </div>
        )}

        {!loading && (
          <>
            {/* Podium */}
            {topThree.length > 0 && (
              <div className="grid grid-cols-3 gap-3 md:gap-5 items-end max-w-lg mx-auto">
                {/* 2nd */}
                {topThree[1] ? (
                  <PodiumCard entry={topThree[1]} place={2} metric={metric} />
                ) : (
                  <div />
                )}
                {/* 1st */}
                {topThree[0] ? (
                  <div className="relative">
                    <motion.div
                      className="absolute -top-6 left-1/2 -translate-x-1/2"
                      animate={{ y: [0, -6, 0] }}
                      transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
                    >
                      <Sparkles className="w-5 h-5 text-yellow-400" />
                    </motion.div>
                    <PodiumCard entry={topThree[0]} place={1} metric={metric} />
                  </div>
                ) : (
                  <div />
                )}
                {/* 3rd */}
                {topThree[2] ? (
                  <PodiumCard entry={topThree[2]} place={3} metric={metric} />
                ) : (
                  <div />
                )}
              </div>
            )}

            {/* Your Position Card */}
            {myRank && myRank.rank !== null && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 }}
                className="relative rounded-2xl border border-brand-orange/20 bg-gradient-to-r from-brand-orange/10 to-transparent p-5 overflow-hidden"
              >
                <motion.div
                  className="absolute top-0 right-0 w-32 h-32 bg-brand-orange/10 blur-3xl rounded-full pointer-events-none"
                  animate={{ opacity: [0.3, 0.6, 0.3] }}
                  transition={{ repeat: Infinity, duration: 3 }}
                />
                <div className="relative z-10 flex flex-col md:flex-row md:items-center gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-brand-orange/20 border-2 border-brand-orange/40 flex items-center justify-center text-lg font-bold text-brand-orange">
                      #{myRank.rank}
                    </div>
                    <div>
                      <p className="text-white font-bold text-lg">{myRank.full_name}</p>
                      <p className="text-sm text-white/60">
                        {myRank.rank === 1
                          ? '¡Sos el líder del equipo! 🏆'
                          : `Sos #${myRank.rank} de ${myRank.total_members} vendedores`}
                      </p>
                    </div>
                  </div>
                  <div className="flex-1" />
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <p className="text-xs text-white/40">Nivel</p>
                      <p className="text-lg font-bold text-white">{myRank.level}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-white/40">{METRIC_LABELS[metric]}</p>
                      <p className="text-lg font-bold text-brand-orange">
                        {formatMetricValue(metric, myRank[metric] as number)}
                      </p>
                    </div>
                  </div>
                </div>
                {overtakeMsg && (
                  <div className="relative z-10 mt-3 flex items-center gap-2 text-sm text-brand-orange">
                    <ArrowUp className="w-4 h-4" />
                    <span>{overtakeMsg}</span>
                  </div>
                )}
              </motion.div>
            )}

            {/* Nearby Competitors */}
            {nearby && nearby.nearby.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Medal className="w-4 h-4 text-white/40" />
                  <h3 className="text-sm font-semibold text-white/70">Cerca de vos</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  <AnimatePresence>
                    {nearby.nearby.map((entry) => (
                      <NearbyCard
                        key={entry.user_id}
                        entry={entry}
                        metric={metric}
                        currentUserId={currentUserId}
                      />
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            )}

            {/* Full Leaderboard Table */}
            {rest.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-white/40" />
                  <h3 className="text-sm font-semibold text-white/70">Tabla completa</h3>
                </div>
                <div className="rounded-2xl border border-white/[0.06] bg-white/[0.01] overflow-hidden">
                  {rest.map((entry, idx) => {
                    const isMe = entry.user_id === currentUserId
                    return (
                      <motion.div
                        key={entry.user_id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.03 }}
                        className={`flex items-center gap-4 px-5 py-3.5 border-b border-white/[0.04] last:border-0 transition-colors ${
                          isMe ? 'bg-brand-orange/5' : 'hover:bg-white/[0.02]'
                        }`}
                      >
                        <span
                          className={`text-sm font-bold w-8 text-center ${
                            entry.rank <= 3 ? 'text-yellow-400' : 'text-white/30'
                          }`}
                        >
                          {entry.rank}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p
                            className={`text-sm font-medium truncate ${
                              isMe ? 'text-brand-orange' : 'text-white'
                            }`}
                          >
                            {entry.full_name}
                            {isMe && (
                              <span className="ml-2 text-[10px] font-bold bg-brand-orange/20 text-brand-orange px-1.5 py-0.5 rounded-md">
                                VOS
                              </span>
                            )}
                          </p>
                          <p className="text-[11px] text-white/30">Nivel {entry.level}</p>
                        </div>
                        <div className="flex items-center gap-5 text-right">
                          <div>
                            <p className="text-xs text-white/40">{METRIC_LABELS[metric]}</p>
                            <p className="text-sm font-bold text-white">
                              {formatMetricValue(metric, entry[metric] as number)}
                            </p>
                          </div>
                          <div className="hidden sm:block">
                            <p className="text-xs text-white/40">Ventas</p>
                            <p className="text-sm text-white/70">{entry.total_sales_closed}</p>
                          </div>
                          <div className="hidden sm:block">
                            <p className="text-xs text-white/40">Racha</p>
                            <p className="text-sm text-white/70 flex items-center gap-1">
                              {entry.current_login_streak > 2 && (
                                <Flame className="w-3 h-3 text-orange-400" />
                              )}
                              {entry.current_login_streak}d
                            </p>
                          </div>
                          <div className="hidden md:block">
                            <p className="text-xs text-white/40">Logros</p>
                            <p className="text-sm text-white/70">{entry.total_achievements}</p>
                          </div>
                          <ChevronRight className="w-4 h-4 text-white/10" />
                        </div>
                      </motion.div>
                    )
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
