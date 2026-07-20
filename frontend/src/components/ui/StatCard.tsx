import { ReactNode } from 'react'

interface StatCardProps {
  label: string
  value: string | number
  icon: ReactNode | any
  trend?: { value: string; isPositive: boolean } | string
  color?: 'orange' | 'teal' | 'violet' | 'blue' | 'emerald' | 'purple' | 'amber'
}

export default function StatCard({ label, value, icon, trend, color = 'orange' }: StatCardProps) {
  const colors: Record<string, string> = {
    orange: 'bg-brand-orange/10 text-brand-orange',
    teal: 'bg-brand-teal/10 text-brand-teal',
    violet: 'bg-brand-violet/10 text-brand-violet',
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    purple: 'bg-purple-500/10 text-purple-400',
    amber: 'bg-amber-500/10 text-amber-400',
  }

  const IconComponent = icon

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-5 hover:bg-white/[0.07] transition-colors">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-white/50">{label}</p>
          <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
          {trend && typeof trend === 'object' && (
            <p className={`text-sm font-medium ${trend.isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend.isPositive ? '↑' : '↓'} {trend.value}
            </p>
          )}
        </div>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color] || colors.orange}`}>
          {typeof IconComponent === 'function' ? <IconComponent className="w-5 h-5" /> : icon}
        </div>
      </div>
    </div>
  )
}
