'use client'

import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle, Zap } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { ChannelGap } from '@/lib/businessContext'

interface ChannelGapListProps {
  gaps: ChannelGap[]
  onCreateMission?: (playbookSlug: string) => void
}

const priorityConfig = {
  critical: { label: 'Crítico', variant: 'destructive' as const, icon: <AlertTriangle className="w-3 h-3" /> },
  high: { label: 'Alto', variant: 'warning' as const, icon: <AlertTriangle className="w-3 h-3" /> },
  medium: { label: 'Medio', variant: 'info' as const, icon: <Zap className="w-3 h-3" /> },
  low: { label: 'Bajo', variant: 'secondary' as const, icon: <CheckCircle className="w-3 h-3" /> },
}

export default function ChannelGapList({ gaps, onCreateMission }: ChannelGapListProps) {
  if (gaps.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <CheckCircle className="w-8 h-8 text-brand-teal mx-auto mb-2" />
          <p className="text-sm text-white/30">¡Todos tus canales están configurados! 🎉</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      {gaps.map((gap, index) => {
        const priority = priorityConfig[gap.priority as keyof typeof priorityConfig] || priorityConfig.medium
        return (
          <motion.div
            key={gap.channel}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card className="border-l-4" style={{ borderLeftColor: gap.priority === 'critical' ? '#EF4444' : gap.priority === 'high' ? '#F59E0B' : '#3B82F6' }}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={priority.variant} className="text-[10px] flex items-center gap-1">
                        {priority.icon}
                        {priority.label}
                      </Badge>
                      <span className="text-sm font-medium text-white capitalize">{gap.channel.replace('_', ' ')}</span>
                    </div>
                    <p className="text-xs text-white/40">{gap.impact_estimate}</p>
                    <p className="text-xs text-white/20 mt-0.5">Dificultad: {gap.setup_difficulty}</p>
                  </div>
                  {gap.recommended_playbook && onCreateMission && (
                    <Button size="sm" onClick={() => gap.recommended_playbook && onCreateMission(gap.recommended_playbook)}>
                      <Zap className="w-3 h-3 mr-1" />
                      Crear misión
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )
      })}
    </div>
  )
}
