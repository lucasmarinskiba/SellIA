'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  Award,
  Trophy,
  Star,
  Globe,
  Loader2,
  CheckCircle2,
  Lock,
  Share2,
  ExternalLink,
  TrendingUp,
  Heart,
} from 'lucide-react'

interface Certification {
  id: string
  slug: string
  name: string
  description: string
  level: string
  category: string
  badge_color: string
}

interface MyCert {
  id: string
  program_name: string
  status: string
  progress_percent: number
  completed_at?: string
  certificate_id?: string
  is_public: boolean
}

export default function AmbassadorPage() {
  const { user, loading: authLoading } = useAuth()
  const [certs, setCerts] = useState<Certification[]>([])
  const [myCerts, setMyCerts] = useState<MyCert[]>([])
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [certsRes, myCertsRes, profileRes] = await Promise.all([
        api.get('/ambassador/certifications'),
        api.get('/ambassador/my-certifications'),
        api.get('/ambassador/profile'),
      ])
      setCerts(certsRes.data)
      setMyCerts(myCertsRes.data)
      setProfile(profileRes.data)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  const publishProfile = async () => {
    try {
      await api.post('/ambassador/profile/publish', {
        headline: profile?.headline,
        bio: profile?.bio,
        specialty: profile?.specialty,
      })
      loadData()
    } catch {
      // silent
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 rounded-xl bg-yellow-500/10">
            <Award className="w-6 h-6 text-yellow-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Ambassador Program</h1>
            <p className="text-sm text-white/50">Convertite en referente de tu industria</p>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
          </div>
        ) : (
          <>
            {/* Public Profile Card */}
            <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Globe className="w-5 h-5 text-white/50" />
                  <h2 className="text-lg font-semibold text-white">Perfil Público de Experto</h2>
                </div>
                {profile?.is_published ? (
                  <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full">
                    <CheckCircle2 className="w-3 h-3" />
                    Publicado
                  </span>
                ) : (
                  <button
                    onClick={publishProfile}
                    className="px-4 py-2 rounded-lg bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors"
                  >
                    Publicar perfil
                  </button>
                )}
              </div>

              {profile && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                    <h3 className="text-white font-semibold">{profile.headline}</h3>
                    <p className="text-sm text-white/50 mt-1">{profile.bio}</p>
                    <div className="flex items-center gap-2 mt-3">
                      <span className="text-xs px-2 py-1 rounded bg-white/[0.05] text-white/50">{profile.specialty}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3 rounded-xl bg-white/[0.02] text-center">
                      <p className="text-lg font-bold text-white">{profile.total_sales_helped}</p>
                      <p className="text-[10px] uppercase tracking-wider text-white/40">Ventas ayudadas</p>
                    </div>
                    <div className="p-3 rounded-xl bg-white/[0.02] text-center">
                      <p className="text-lg font-bold text-white">${profile.total_revenue_helped}</p>
                      <p className="text-[10px] uppercase tracking-wider text-white/40">Revenue generado</p>
                    </div>
                    <div className="p-3 rounded-xl bg-white/[0.02] text-center">
                      <p className="text-lg font-bold text-white">{profile.view_count}</p>
                      <p className="text-[10px] uppercase tracking-wider text-white/40">Visitas al perfil</p>
                    </div>
                  </div>

                  {profile.is_published && profile.slug && (
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                      <ExternalLink className="w-4 h-4 text-white/30" />
                      <span className="text-sm text-white/50">tu-perfil.sellia.com/expert/{profile.slug}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Certifications */}
            <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
              <div className="flex items-center gap-3 mb-6">
                <Trophy className="w-5 h-5 text-white/50" />
                <h2 className="text-lg font-semibold text-white">Certificaciones</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {certs.map((cert) => {
                  const myCert = myCerts.find((mc) => mc.program_name === cert.name)
                  const isCompleted = myCert?.status === 'completed'
                  const inProgress = myCert?.status === 'in_progress'

                  return (
                    <div
                      key={cert.id}
                      className={`p-4 rounded-xl border transition-colors ${
                        isCompleted
                          ? 'bg-white/[0.03] border-white/[0.08]'
                          : 'bg-white/[0.02] border-white/[0.04] opacity-70'
                      }`}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div
                          className="w-10 h-10 rounded-lg flex items-center justify-center"
                          style={{ backgroundColor: cert.badge_color + '20' }}
                        >
                          <Award className="w-5 h-5" style={{ color: cert.badge_color }} />
                        </div>
                        <div>
                          <h3 className="text-sm font-semibold text-white">{cert.name}</h3>
                          <p className="text-[10px] uppercase tracking-wider text-white/40">{cert.level} · {cert.category}</p>
                        </div>
                      </div>

                      <p className="text-xs text-white/50 mb-3 line-clamp-2">{cert.description}</p>

                      {isCompleted ? (
                        <div className="flex items-center gap-2 text-xs text-emerald-400">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Completada
                          {myCert.certificate_id && (
                            <span className="text-white/30 ml-auto">{myCert.certificate_id}</span>
                          )}
                        </div>
                      ) : inProgress ? (
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-white/50">En progreso</span>
                            <span className="text-white">{myCert.progress_percent}%</span>
                          </div>
                          <div className="h-1.5 rounded-full bg-white/[0.05]">
                            <div
                              className="h-full rounded-full bg-brand-orange"
                              style={{ width: `${myCert.progress_percent}%` }}
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-xs text-white/30">
                          <Lock className="w-3.5 h-3.5" />
                          No iniciada
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
