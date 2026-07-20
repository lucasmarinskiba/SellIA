'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { objectivesApi, Department, BusinessObjective, KPI } from '@/lib/objectives'
import {
  Target, TrendingUp, AlertCircle, Loader2, X, Plus,
  Briefcase, ChevronRight, BarChart3, Layers
} from 'lucide-react'

export default function ObjetivosPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [departments, setDepartments] = useState<Department[]>([])
  const [objectives, setObjectives] = useState<BusinessObjective[]>([])
  const [kpis, setKpis] = useState<KPI[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => setError('No se pudieron cargar los negocios'))
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId])

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [depts, objs, kpiList] = await Promise.all([
        objectivesApi.getDepartments(selectedBusinessId),
        objectivesApi.getObjectives(selectedBusinessId),
        objectivesApi.getKPIs(selectedBusinessId),
      ])
      setDepartments(depts)
      setObjectives(objs)
      setKpis(kpiList)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar objetivos')
    } finally {
      setLoading(false)
    }
  }

  const activeObjectives = objectives.filter(o => o.status === 'active')

  return (
    <div className="space-y-8 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">🎯 Objetivos & KPIs</h1>
          <p className="text-sm text-white/40">Departamentos, objetivos y métricas clave de tu empresa virtual.</p>
        </div>
        <div className="flex items-center gap-3">
          {businesses.length > 0 && (
            <select
              value={selectedBusinessId}
              onChange={e => setSelectedBusinessId(e.target.value)}
              className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
            >
              {businesses.map(b => (
                <option key={b.id} value={b.id} className="bg-[#0A0E1A]">{b.name}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
        </div>
      ) : (
        <>
          {/* Departments */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-brand-orange" />
              Departamentos
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {departments.map(dept => (
                <motion.div
                  key={dept.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass-card p-5 border-l-4"
                  style={{ borderLeftColor: dept.color }}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                      style={{ backgroundColor: dept.color + '20', color: dept.color }}>
                      {dept.icon}
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white">{dept.name}</h3>
                      <p className="text-xs text-white/30">{dept.slug}</p>
                    </div>
                  </div>
                  <p className="text-xs text-white/40 line-clamp-2">{dept.description || 'Sin descripción'}</p>
                </motion.div>
              ))}
              {departments.length === 0 && (
                <div className="glass-card p-5 text-center text-white/20 text-sm col-span-full">
                  No hay departamentos configurados aún.
                </div>
              )}
            </div>
          </div>

          {/* Objectives */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Target className="w-5 h-5 text-brand-violet" />
              Objetivos Activos
              <span className="text-xs text-white/30 font-normal ml-2">({activeObjectives.length})</span>
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {activeObjectives.map(obj => {
                const pct = obj.target_value > 0 ? (obj.current_value / obj.target_value) * 100 : 0
                const statusColor = pct >= 80 ? 'text-brand-teal' : pct >= 50 ? 'text-yellow-400' : 'text-red-400'
                const barColor = pct >= 80 ? '#00D4AA' : pct >= 50 ? '#F59E0B' : '#EF4444'
                return (
                  <motion.div
                    key={obj.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card p-5"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-semibold text-white">{obj.name}</h3>
                        <p className="text-xs text-white/30">{obj.description || 'Sin descripción'}</p>
                      </div>
                      <span className={`text-xs font-bold ${statusColor}`}>{pct.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-white/40 mb-2">
                      <span>{obj.current_value.toLocaleString()} / {obj.target_value.toLocaleString()} {obj.unit}</span>
                      <span className="capitalize">{obj.period}</span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(pct, 100)}%` }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: barColor }}
                        transition={{ duration: 0.8 }}
                      />
                    </div>
                  </motion.div>
                )
              })}
              {activeObjectives.length === 0 && (
                <div className="glass-card p-5 text-center text-white/20 text-sm col-span-full">
                  No hay objetivos activos.
                </div>
              )}
            </div>
          </div>

          {/* KPIs */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-brand-teal" />
              KPIs
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {kpis.map(kpi => {
                const target = kpi.target_value || 1
                const pct = (kpi.current_value / target) * 100
                return (
                  <motion.div
                    key={kpi.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card p-5"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Layers className="w-4 h-4 text-white/30" />
                      <h3 className="text-sm font-semibold text-white truncate">{kpi.name}</h3>
                    </div>
                    <p className="text-xs text-white/30 mb-3">{kpi.metric_type} · {kpi.aggregation}</p>
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-2xl font-bold text-white">{kpi.current_value.toLocaleString()}</p>
                        <p className="text-xs text-white/30">meta: {target.toLocaleString()} {kpi.unit}</p>
                      </div>
                      <span className={`text-xs font-bold ${pct >= 80 ? 'text-brand-teal' : pct >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {pct.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-brand-orange"
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </motion.div>
                )
              })}
              {kpis.length === 0 && (
                <div className="glass-card p-5 text-center text-white/20 text-sm col-span-full">
                  No hay KPIs configurados.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
