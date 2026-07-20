'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { Bot, Mic, Volume2, Activity, Loader2 } from 'lucide-react'
import { SellIASessionState } from '@/hooks/useSellIASession'

interface SellIAAvatarProps {
  state: SellIASessionState
  size?: 'sm' | 'md' | 'lg' | 'xl'
  onClick?: () => void
}

const SIZE_MAP = {
  sm: { container: 48, icon: 20, ring: 44 },
  md: { container: 64, icon: 28, ring: 58 },
  lg: { container: 96, icon: 40, ring: 88 },
  xl: { container: 140, icon: 56, ring: 130 },
}

const STATE_CONFIG: Record<SellIASessionState, { color1: string; color2: string; speed: number; icon: any }> = {
  idle: { color1: '#FF6B35', color2: '#E55A2B', speed: 12, icon: Bot },
  greeting: { color1: '#FF6B35', color2: '#a855f7', speed: 4, icon: Volume2 },
  awaiting_confirmation: { color1: '#00D4AA', color2: '#10b981', speed: 2, icon: Mic },
  thinking: { color1: '#FF6B35', color2: '#a855f7', speed: 1.5, icon: Loader2 },
  working: { color1: '#3b82f6', color2: '#00D4AA', speed: 3, icon: Activity },
  speaking: { color1: '#FF6B35', color2: '#FF8C5A', speed: 2, icon: Volume2 },
}

export default function SellIAAvatar({ state, size = 'lg', onClick }: SellIAAvatarProps) {
  const s = SIZE_MAP[size]
  const cfg = STATE_CONFIG[state]
  const Icon = cfg.icon
  const isAnimated = state !== 'idle'

  return (
    <motion.div
      className="relative flex items-center justify-center cursor-pointer select-none"
      style={{ width: s.container, height: s.container }}
      onClick={onClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {/* Glow background */}
      <AnimatePresence>
        {isAnimated && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 0.25, scale: 1.2 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.5 }}
            className="absolute inset-0 rounded-full blur-2xl"
            style={{ background: `radial-gradient(circle, ${cfg.color1}, transparent)` }}
          />
        )}
      </AnimatePresence>

      {/* Outer rotating ring */}
      <svg
        className="absolute inset-0"
        style={{
          width: s.container,
          height: s.container,
          animation: `spin ${cfg.speed}s linear infinite`,
        }}
        viewBox={`0 0 ${s.container} ${s.container}`}
      >
        <defs>
          <linearGradient id={`ringGrad-${state}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={cfg.color1} />
            <stop offset="100%" stopColor={cfg.color2} />
          </linearGradient>
        </defs>
        <circle
          cx={s.container / 2}
          cy={s.container / 2}
          r={s.ring / 2}
          fill="none"
          stroke={`url(#ringGrad-${state})`}
          strokeWidth={size === 'xl' ? 2.5 : size === 'lg' ? 2 : 1.5}
          strokeDasharray={`${s.ring * 0.6} ${s.ring * 0.9}`}
          strokeLinecap="round"
          opacity={isAnimated ? 1 : 0.5}
        />
      </svg>

      {/* Inner solid ring */}
      <div
        className="absolute rounded-full border"
        style={{
          width: s.ring - 8,
          height: s.ring - 8,
          borderColor: `${cfg.color1}40`,
          background: `linear-gradient(135deg, ${cfg.color1}20, ${cfg.color2}15)`,
        }}
      />

      {/* Icon */}
      <motion.div
        className="relative z-10 flex items-center justify-center"
        animate={
          state === 'awaiting_confirmation'
            ? { scale: [1, 1.15, 1] }
            : state === 'working'
            ? { rotate: [0, 360] }
            : {}
        }
        transition={
          state === 'awaiting_confirmation'
            ? { duration: 1.2, repeat: Infinity }
            : state === 'working'
            ? { duration: 8, repeat: Infinity, ease: 'linear' }
            : {}
        }
      >
        <Icon
          size={s.icon}
          style={{
            color: cfg.color1,
            filter: `drop-shadow(0 0 ${size === 'xl' ? 12 : 6}px ${cfg.color1}80)`,
          }}
        />
      </motion.div>

      {/* Status dot */}
      <AnimatePresence>
        {state === 'working' && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-emerald-400 border-2 border-[#0A0E1A]"
            style={
              size === 'xl'
                ? { width: 18, height: 18, borderWidth: 3 }
                : {}
            }
          >
            <motion.div
              className="absolute inset-0 rounded-full bg-emerald-400"
              animate={{ scale: [1, 1.6, 1], opacity: [0.6, 0, 0.6] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sound waves when listening */}
      <AnimatePresence>
        {state === 'awaiting_confirmation' && (
          <>
            {[0, 1, 2].map(i => (
              <motion.div
                key={i}
                className="absolute rounded-full border-2"
                style={{ borderColor: `${cfg.color1}30` }}
                initial={{ width: s.container, height: s.container, opacity: 0.6 }}
                animate={{
                  width: s.container + 40 + i * 20,
                  height: s.container + 40 + i * 20,
                  opacity: 0,
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  delay: i * 0.4,
                  ease: 'easeOut',
                }}
              />
            ))}
          </>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
