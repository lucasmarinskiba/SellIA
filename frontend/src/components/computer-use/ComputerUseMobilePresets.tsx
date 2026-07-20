"use client"

import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Smartphone, Monitor, Tablet } from "lucide-react"

interface Preset {
  id: string
  name: string
  icon: React.ReactNode
  viewport: { width: number; height: number }
}

const PRESETS: Preset[] = [
  { id: "desktop_hd", name: "Desktop HD", icon: <Monitor className="w-4 h-4" />, viewport: { width: 1920, height: 1080 } },
  { id: "iphone_14", name: "iPhone 14", icon: <Smartphone className="w-4 h-4" />, viewport: { width: 390, height: 844 } },
  { id: "iphone_14_pro_max", name: "iPhone 14 Pro Max", icon: <Smartphone className="w-4 h-4" />, viewport: { width: 430, height: 932 } },
  { id: "ipad_pro", name: "iPad Pro", icon: <Tablet className="w-4 h-4" />, viewport: { width: 1024, height: 1366 } },
  { id: "pixel_7", name: "Pixel 7", icon: <Smartphone className="w-4 h-4" />, viewport: { width: 412, height: 915 } },
  { id: "samsung_s23", name: "Galaxy S23", icon: <Smartphone className="w-4 h-4" />, viewport: { width: 384, height: 854 } },
]

interface Props {
  selected: string
  onSelect: (presetId: string) => void
}

export default function ComputerUseMobilePresets({ selected, onSelect }: Props) {
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-white/50 uppercase tracking-wider">Dispositivo</h4>
      <div className="grid grid-cols-3 gap-1.5">
        {PRESETS.map(preset => (
          <button
            key={preset.id}
            onClick={() => onSelect(preset.id)}
            className={`flex flex-col items-center gap-1 p-2 rounded-lg border text-xs transition-colors ${
              selected === preset.id
                ? "bg-blue-500/20 border-blue-500/40 text-blue-400"
                : "bg-white/5 border-white/[0.06] text-white/40 hover:bg-white/[0.08] hover:text-white/60"
            }`}
            title={`${preset.name} (${preset.viewport.width}x${preset.viewport.height})`}
          >
            {preset.icon}
            <span className="text-[10px] truncate w-full text-center">{preset.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
