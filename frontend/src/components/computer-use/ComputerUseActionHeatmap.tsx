"use client"

import { useMemo } from "react"

interface ActionPoint {
  x: number
  y: number
  count: number
}

interface Props {
  actions: ActionPoint[]
  width: number
  height: number
  imageUrl?: string
}

export default function ComputerUseActionHeatmap({ actions, width, height, imageUrl }: Props) {
  const maxCount = useMemo(() => Math.max(...actions.map(a => a.count), 1), [actions])

  const getColor = (count: number) => {
    const intensity = count / maxCount
    // Blue (low) -> Green -> Yellow -> Red (high)
    if (intensity < 0.33) return `rgba(59, 130, 246, ${0.3 + intensity})`
    if (intensity < 0.66) return `rgba(34, 197, 94, ${0.3 + intensity})`
    return `rgba(239, 68, 68, ${0.3 + intensity})`
  }

  return (
    <div className="relative" style={{ width, height }}>
      {imageUrl && (
        <img src={imageUrl} alt="Base" className="absolute inset-0 w-full h-full object-contain opacity-30" />
      )}
      <svg width={width} height={height} className="absolute inset-0">
        {actions.map((action, i) => (
          <circle
            key={i}
            cx={action.x}
            cy={action.y}
            r={8 + action.count * 3}
            fill={getColor(action.count)}
            stroke="white"
            strokeWidth={0.5}
            opacity={0.7}
          />
        ))}
      </svg>
      {/* Legend */}
      <div className="absolute bottom-2 right-2 bg-black/70 rounded-lg p-2 text-[10px] text-white/60">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-blue-500" /> Bajo
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-green-500" /> Medio
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-red-500" /> Alto
        </div>
      </div>
    </div>
  )
}
