'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { Volume2, Bot, Loader2 } from 'lucide-react'

interface SellIANarrationBarProps {
  text: string
  isSpeaking?: boolean
  isTyping?: boolean
}

export default function SellIANarrationBar({ text, isSpeaking = false, isTyping = false }: SellIANarrationBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="absolute bottom-3 left-3 right-3 z-20 px-4 py-2.5 rounded-xl bg-black/70 backdrop-blur-md border border-white/[0.08] flex items-center gap-3"
    >
      <div className="w-7 h-7 rounded-full bg-brand-orange/20 border border-brand-orange/30 flex items-center justify-center shrink-0">
        {isSpeaking ? (
          <Volume2 className="w-3.5 h-3.5 text-brand-orange animate-pulse" />
        ) : isTyping ? (
          <Loader2 className="w-3.5 h-3.5 text-brand-orange animate-spin" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-brand-orange" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/80 leading-relaxed">
          <span className="text-white/40 text-xs mr-2 font-mono">SELLIA&gt;</span>
          <TypewriterText text={text} enabled={isTyping} />
        </p>
      </div>

      {/* Voice wave animation when speaking */}
      <AnimatePresence>
        {isSpeaking && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-end gap-0.5 h-4"
          >
            {[0, 1, 2, 3, 2, 1].map((h, i) => (
              <motion.div
                key={i}
                className="w-0.5 rounded-full bg-brand-orange"
                animate={{ height: [4, 8 + h * 3, 4] }}
                transition={{
                  duration: 0.5,
                  repeat: Infinity,
                  delay: i * 0.08,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function TypewriterText({ text, enabled }: { text: string; enabled: boolean }) {
  if (!enabled) return <>{text}</>

  return (
    <span>
      {text}
      <motion.span
        className="inline-block w-0.5 h-4 bg-brand-orange ml-0.5 align-middle"
        animate={{ opacity: [1, 0] }}
        transition={{ duration: 0.5, repeat: Infinity }}
      />
    </span>
  )
}
