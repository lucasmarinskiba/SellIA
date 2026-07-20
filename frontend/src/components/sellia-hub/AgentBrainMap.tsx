'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Bot, MessageSquare, Camera as Instagram, Mail, BarChart3,
  ShoppingCart, FileText, Zap, Shield, Target,
  Package, Handshake, TrendingUp, Activity
} from 'lucide-react'

export interface BrainNode {
  id: string
  name: string
  icon: string
  status: 'active' | 'idle' | 'warning' | 'error'
  color: string
  connections: string[]
  metric?: string
}

interface AgentBrainMapProps {
  nodes: BrainNode[]
  centerLabel?: string
}

const ICON_MAP: Record<string, any> = {
  bot: Bot,
  message: MessageSquare,
  instagram: Instagram,
  mail: Mail,
  chart: BarChart3,
  cart: ShoppingCart,
  file: FileText,
  zap: Zap,
  shield: Shield,
  target: Target,
  package: Package,
  handshake: Handshake,
  trend: TrendingUp,
  activity: Activity,
}

const STATUS_COLOR: Record<string, string> = {
  active: '#10b981',
  idle: '#6b7280',
  warning: '#f59e0b',
  error: '#ef4444',
}

export default function AgentBrainMap({ nodes, centerLabel = 'SellIA' }: AgentBrainMapProps) {
  const positionedNodes = useMemo(() => {
    const count = nodes.length
    const radius = 90
    return nodes.map((node, i) => {
      const angle = (i / count) * 2 * Math.PI - Math.PI / 2
      return {
        ...node,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
      }
    })
  }, [nodes])

  return (
    <div className="relative w-full aspect-square max-w-[280px] mx-auto">
      {/* SVG connections */}
      <svg className="absolute inset-0 w-full h-full" viewBox="-140 -140 280 280">
        {/* Lines from center to nodes */}
        {positionedNodes.map(node => (
          <motion.line
            key={`line-${node.id}`}
            x1={0}
            y1={0}
            x2={node.x}
            y2={node.y}
            stroke={node.status === 'active' ? node.color : '#ffffff10'}
            strokeWidth={node.status === 'active' ? 1.5 : 1}
            strokeDasharray={node.status === 'active' ? '4 4' : '2 4'}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.5, delay: 0.2 }}
          />
        ))}

        {/* Inter-node connections */}
        {positionedNodes.map(node =>
          node.connections.map(targetId => {
            const target = positionedNodes.find(n => n.id === targetId)
            if (!target) return null
            return (
              <motion.line
                key={`conn-${node.id}-${targetId}`}
                x1={node.x}
                y1={node.y}
                x2={target.x}
                y2={target.y}
                stroke="#ffffff08"
                strokeWidth={0.5}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1 }}
              />
            )
          })
        )}
      </svg>

      {/* Center core */}
      <div className="absolute inset-0 flex items-center justify-center">
        <motion.div
          className="relative w-16 h-16 rounded-full flex items-center justify-center"
          style={{
            background: 'linear-gradient(135deg, #FF6B3520, #a855f720)',
            border: '1.5px solid #FF6B3540',
          }}
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <Bot className="w-7 h-7 text-brand-orange" style={{ filter: 'drop-shadow(0 0 8px rgba(255,107,53,0.5))' }} />
          {/* Pulse ring */}
          <motion.div
            className="absolute inset-0 rounded-full border border-brand-orange/20"
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </motion.div>
      </div>

      {/* Nodes */}
      {positionedNodes.map((node, i) => {
        const Icon = ICON_MAP[node.icon] || Bot
        const isActive = node.status === 'active'

        return (
          <motion.div
            key={node.id}
            className="absolute"
            style={{
              left: '50%',
              top: '50%',
              marginLeft: node.x - 20,
              marginTop: node.y - 20,
            }}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.08 + 0.3, type: 'spring' }}
          >
            <div className="relative group">
              {/* Glow */}
              {isActive && (
                <div
                  className="absolute inset-0 rounded-xl blur-lg opacity-30"
                  style={{ background: node.color }}
                />
              )}

              {/* Node card */}
              <div
                className="relative w-10 h-10 rounded-xl flex items-center justify-center border transition-all cursor-pointer hover:scale-110"
                style={{
                  background: `${node.color}15`,
                  borderColor: isActive ? `${node.color}50` : '#ffffff10',
                }}
                title={node.name}
              >
                <Icon className="w-4 h-4" style={{ color: isActive ? node.color : '#ffffff40' }} />

                {/* Status dot */}
                <div
                  className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border border-[#0A0E1A]"
                  style={{ background: STATUS_COLOR[node.status] }}
                />
              </div>

              {/* Tooltip */}
              <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 px-2 py-1 rounded-md bg-black/80 border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                <p className="text-[9px] text-white/80 font-medium">{node.name}</p>
                {node.metric && (
                  <p className="text-[8px] text-white/40">{node.metric}</p>
                )}
              </div>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
