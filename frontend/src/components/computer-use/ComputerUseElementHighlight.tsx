"use client"

import { useEffect, useState } from "react"

interface Props {
  x: number
  y: number
  width?: number
  height?: number
  color?: string
  label?: string
  pulse?: boolean
}

export default function ComputerUseElementHighlight({
  x,
  y,
  width = 40,
  height = 40,
  color = "#f59e0b",
  label,
  pulse = true,
}: Props) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    setVisible(true)
    const timer = setTimeout(() => setVisible(false), 2000)
    return () => clearTimeout(timer)
  }, [x, y])

  if (!visible) return null

  return (
    <div
      className={`absolute pointer-events-none z-20 ${pulse ? "animate-pulse" : ""}`}
      style={{
        left: x - width / 2,
        top: y - height / 2,
        width,
        height,
        border: `2px solid ${color}`,
        borderRadius: 4,
        boxShadow: `0 0 0 2px ${color}40, 0 0 20px ${color}60`,
        backgroundColor: `${color}15`,
      }}
    >
      {label && (
        <div
          className="absolute -top-6 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded text-[10px] font-bold whitespace-nowrap"
          style={{ backgroundColor: color, color: "#000" }}
        >
          {label}
        </div>
      )}
      {/* Crosshair center */}
      <div
        className="absolute top-1/2 left-1/2 w-1.5 h-1.5 rounded-full -translate-x-1/2 -translate-y-1/2"
        style={{ backgroundColor: color }}
      />
    </div>
  )
}
