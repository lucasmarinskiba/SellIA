'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Rocket,
  Search,
  Megaphone,
  ShoppingCart,
  Globe,
  Palette,
  Truck,
  Cpu,
  Clock,
  BarChart3,
  X,
  Gauge,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Playbook, MissionCategory } from '@/lib/missions'

const categoryIcons: Record<MissionCategory, React.ReactNode> = {
  launch: <Rocket className="w-4 h-4" />,
  seo: <Search className="w-4 h-4" />,
  ads: <Megaphone className="w-4 h-4" />,
  recovery: <ShoppingCart className="w-4 h-4" />,
  expansion: <Globe className="w-4 h-4" />,
  branding: <Palette className="w-4 h-4" />,
  logistics: <Truck className="w-4 h-4" />,
  automation: <Cpu className="w-4 h-4" />,
}

const categoryLabels: Record<MissionCategory, string> = {
  launch: 'Lanzamiento',
  seo: 'SEO',
  ads: 'Publicidad',
  recovery: 'Recuperación',
  expansion: 'Expansión',
  branding: 'Branding',
  logistics: 'Logística',
  automation: 'Automatización',
}

function getDifficultyLabel(minutes: number) {
  if (minutes <= 90) return 'Fácil'
  if (minutes <= 150) return 'Medio'
  return 'Avanzado'
}

function getDifficultyVariant(minutes: number): 'success' | 'warning' | 'destructive' {
  if (minutes <= 90) return 'success'
  if (minutes <= 150) return 'warning'
  return 'destructive'
}

interface PlaybookSelectorProps {
  playbooks: Playbook[]
  onSelect: (playbook: Playbook) => void
  onClose: () => void
}

export default function PlaybookSelector({ playbooks, onSelect, onClose }: PlaybookSelectorProps) {
  const [filter, setFilter] = useState<MissionCategory | 'all'>('all')
  const [search, setSearch] = useState('')

  const categories = ['all', ...Array.from(new Set(playbooks.map(p => p.category)))] as (MissionCategory | 'all')[]

  const filtered = playbooks.filter((pb) => {
    const matchCategory = filter === 'all' || pb.category === filter
    const matchSearch = !search || pb.name.toLowerCase().includes(search.toLowerCase()) || pb.description.toLowerCase().includes(search.toLowerCase())
    return matchCategory && matchSearch
  })

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="w-full max-w-3xl max-h-[80vh] overflow-y-auto bg-[#0c0e1a] border border-white/10 rounded-3xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 bg-[#0c0e1a]/95 backdrop-blur-md border-b border-white/5 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-white">🎯 Playbooks de Misiones</h2>
              <p className="text-sm text-white/40 mt-1">Selecciona una estrategia predefinida para tu negocio</p>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>

          <input
            type="text"
            placeholder="Buscar playbook..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20 mb-3"
          />

          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  filter === cat
                    ? 'bg-brand-orange/20 text-brand-orange border border-brand-orange/20'
                    : 'bg-white/5 text-white/40 border border-white/5 hover:bg-white/10'
                }`}
              >
                {cat === 'all' ? 'Todas' : categoryLabels[cat]}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <AnimatePresence>
            {filtered.map((playbook, index) => (
              <motion.div
                key={playbook.slug}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ delay: index * 0.03 }}
              >
                <Card
                  className="cursor-pointer hover:border-brand-orange/30 transition-all duration-200 h-full"
                  onClick={() => onSelect(playbook)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-brand-orange/10 flex items-center justify-center text-brand-orange">
                          {categoryIcons[playbook.category]}
                        </div>
                        <CardTitle className="text-sm">{playbook.name}</CardTitle>
                      </div>
                      <Badge variant={getDifficultyVariant(playbook.estimated_duration_minutes)} className="text-[10px]">
                        {getDifficultyLabel(playbook.estimated_duration_minutes)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pb-3">
                    <p className="text-xs text-white/50 line-clamp-2 mb-3">{playbook.description}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex flex-wrap gap-1">
                        {playbook.platforms.slice(0, 3).map((p) => (
                          <Badge key={p} variant="secondary" className="text-[10px] capitalize">
                            {p}
                          </Badge>
                        ))}
                        {playbook.platforms.length > 3 && (
                          <Badge variant="secondary" className="text-[10px]">
                            +{playbook.platforms.length - 3}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1 text-xs text-white/30">
                        <Gauge className="w-3 h-3" />
                        {Math.round(playbook.estimated_duration_minutes / 60)}h
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {filtered.length === 0 && (
          <div className="p-12 text-center">
            <BarChart3 className="w-8 h-8 text-white/20 mx-auto mb-3" />
            <p className="text-sm text-white/30">No se encontraron playbooks</p>
          </div>
        )}
      </motion.div>
    </motion.div>
  )
}
