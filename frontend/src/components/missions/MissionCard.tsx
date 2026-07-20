'use client'

import { motion } from 'framer-motion'
import {
  Rocket,
  Search,
  Megaphone,
  ShoppingCart,
  Globe,
  Palette,
  Truck,
  Cpu,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  AlertTriangle,
  ChevronRight,
} from 'lucide-react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Mission, MissionCategory, MissionStatus } from '@/lib/missions'

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

const statusConfig: Record<MissionStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'destructive' | 'secondary' | 'info'; icon: React.ReactNode }> = {
  draft: { label: 'Borrador', variant: 'secondary', icon: <Clock className="w-3 h-3" /> },
  proposed: { label: 'Propuesta', variant: 'info', icon: <AlertTriangle className="w-3 h-3" /> },
  approved: { label: 'Aprobada', variant: 'warning', icon: <CheckCircle className="w-3 h-3" /> },
  running: { label: 'En ejecución', variant: 'default', icon: <Loader2 className="w-3 h-3 animate-spin" /> },
  completed: { label: 'Completada', variant: 'success', icon: <CheckCircle className="w-3 h-3" /> },
  failed: { label: 'Fallida', variant: 'destructive', icon: <XCircle className="w-3 h-3" /> },
  cancelled: { label: 'Cancelada', variant: 'secondary', icon: <XCircle className="w-3 h-3" /> },
}

interface MissionCardProps {
  mission: Mission
  onApprove?: (id: string) => void
  onRun?: (id: string) => void
  onCancel?: (id: string) => void
  onClick?: (mission: Mission) => void
  index?: number
}

export default function MissionCard({ mission, onApprove, onRun, onCancel, onClick, index = 0 }: MissionCardProps) {
  const status = statusConfig[mission.status]
  const completedSteps = mission.steps?.filter(s => s.status === 'completed').length || 0
  const totalSteps = mission.steps?.length || 0
  const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card
        className="group cursor-pointer hover:border-brand-orange/30 transition-all duration-300"
        onClick={() => onClick?.(mission)}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-brand-orange">
                {categoryIcons[mission.category]}
              </div>
              <div>
                <CardTitle className="text-base line-clamp-1">{mission.title}</CardTitle>
                <p className="text-xs text-white/40 mt-0.5">
                  {categoryLabels[mission.category]} · {new Date(mission.created_at).toLocaleDateString('es-AR')}
                </p>
              </div>
            </div>
            <Badge variant={status.variant} className="shrink-0 flex items-center gap-1">
              {status.icon}
              {status.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="pb-3">
          {mission.description && (
            <p className="text-sm text-white/50 line-clamp-2 mb-3">{mission.description}</p>
          )}

          <div className="flex flex-wrap gap-1.5 mb-3">
            {mission.target_platforms.map((platform) => (
              <Badge key={platform} variant="secondary" className="text-[10px] capitalize">
                {platform}
              </Badge>
            ))}
          </div>

          {totalSteps > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs text-white/40">
                <span>Progreso</span>
                <span>{completedSteps}/{totalSteps} pasos</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-brand-orange to-brand-violet"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                />
              </div>
            </div>
          )}

          {mission.expected_impact?.revenue_estimate && (
            <div className="mt-3 p-2 rounded-lg bg-brand-teal/5 border border-brand-teal/10">
              <p className="text-xs text-brand-teal font-medium">
                💰 Impacto estimado: ${mission.expected_impact.revenue_estimate.toLocaleString('es-AR')}
              </p>
            </div>
          )}
        </CardContent>

        <CardFooter className="pt-0 gap-2">
          {mission.status === 'proposed' && onApprove && (
            <Button size="sm" className="flex-1" onClick={(e) => { e.stopPropagation(); onApprove(mission.id) }}>
              <CheckCircle className="w-3.5 h-3.5 mr-1" />
              Aprobar
            </Button>
          )}
          {mission.status === 'approved' && onRun && (
            <Button size="sm" className="flex-1" onClick={(e) => { e.stopPropagation(); onRun(mission.id) }}>
              <Play className="w-3.5 h-3.5 mr-1" />
              Ejecutar
            </Button>
          )}
          {(mission.status === 'running' || mission.status === 'approved') && onCancel && (
            <Button size="sm" variant="secondary" className="flex-1" onClick={(e) => { e.stopPropagation(); onCancel(mission.id) }}>
              <XCircle className="w-3.5 h-3.5 mr-1" />
              Cancelar
            </Button>
          )}
          <Button size="sm" variant="ghost" className="px-2" onClick={(e) => { e.stopPropagation(); onClick?.(mission) }}>
            <ChevronRight className="w-4 h-4" />
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  )
}
