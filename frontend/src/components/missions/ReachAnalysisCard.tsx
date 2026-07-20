'use client'

import { motion } from 'framer-motion'
import { Globe, MapPin, TrendingUp, Truck, Package, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { ReachAnalysis } from '@/lib/businessContext'

interface ReachAnalysisCardProps {
  analysis: ReachAnalysis
}

export default function ReachAnalysisCard({ analysis }: ReachAnalysisCardProps) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-brand-orange" />
            <CardTitle className="text-base">Análisis de Alcance</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-white/5">
              <p className="text-xs text-white/40 mb-1">Alcance actual</p>
              <div className="flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5 text-white/60" />
                <span className="text-sm font-medium text-white capitalize">{analysis.current_reach}</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-brand-orange/5 border border-brand-orange/10">
              <p className="text-xs text-brand-orange/60 mb-1">Recomendado</p>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5 text-brand-orange" />
                <span className="text-sm font-medium text-brand-orange capitalize">{analysis.recommended_reach}</span>
              </div>
            </div>
          </div>

          {analysis.cross_border_opportunity && (
            <div className="flex items-start gap-2 p-2 rounded-lg bg-brand-violet/5 border border-brand-violet/10">
              <Package className="w-4 h-4 text-brand-violet mt-0.5 shrink-0" />
              <p className="text-xs text-brand-violet/80">
                🌍 Oportunidad de cross-border detectada. Podés vender en países vecinos con poca inversión adicional.
              </p>
            </div>
          )}

          {analysis.local_seo_priority && (
            <div className="flex items-start gap-2 p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
              <MapPin className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
              <p className="text-xs text-emerald-400/80">
                📍 Tenés presencia física — el SEO local debería ser tu prioridad #1 para atraer clientes cercanos.
              </p>
            </div>
          )}

          {analysis.shipping_recommendations.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-white/40 flex items-center gap-1">
                <Truck className="w-3 h-3" />
                Recomendaciones de envío
              </p>
              {analysis.shipping_recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-white/50">
                  <span className="text-brand-orange mt-0.5">•</span>
                  {rec}
                </div>
              ))}
            </div>
          )}

          <div className="flex flex-wrap gap-1.5">
            {analysis.platform_recommendations.map((plat) => (
              <Badge key={plat} variant="secondary" className="text-[10px]">
                {plat}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
