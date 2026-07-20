"use client"

import { useState } from "react"
import { X, ChevronLeft, ChevronRight, Download } from "lucide-react"

interface Screenshot {
  step: number
  url: string
  image: string
}

interface Props {
  screenshots: Screenshot[]
  onClose: () => void
}

export default function ComputerUseScreenshotGallery({ screenshots, onClose }: Props) {
  const [selected, setSelected] = useState(0)

  const current = screenshots[selected]

  const downloadCurrent = () => {
    const a = document.createElement("a")
    a.href = current.image
    a.download = `step_${current.step}.jpg`
    a.click()
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/95 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-white text-sm">
          Gallery — {selected + 1} / {screenshots.length}
        </span>
        <div className="flex items-center gap-2">
          <button onClick={downloadCurrent} className="p-2 text-white/60 hover:text-white transition-colors">
            <Download className="w-4 h-4" />
          </button>
          <button onClick={onClose} className="p-2 text-white/60 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Image */}
      <div className="flex-1 flex items-center justify-center p-4 relative">
        <button
          onClick={() => setSelected(Math.max(0, selected - 1))}
          disabled={selected === 0}
          className="absolute left-4 p-2 bg-white/10 rounded-full text-white disabled:opacity-20 hover:bg-white/20 transition-colors"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>

        {current && (
          <img
            src={current.image}
            alt={`Step ${current.step}`}
            className="max-w-full max-h-full object-contain rounded-lg"
          />
        )}

        <button
          onClick={() => setSelected(Math.min(screenshots.length - 1, selected + 1))}
          disabled={selected === screenshots.length - 1}
          className="absolute right-4 p-2 bg-white/10 rounded-full text-white disabled:opacity-20 hover:bg-white/20 transition-colors"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      </div>

      {/* Thumbnail strip */}
      <div className="h-24 bg-black/50 border-t border-white/10 overflow-x-auto">
        <div className="flex gap-2 p-2">
          {screenshots.map((s, i) => (
            <button
              key={s.step}
              onClick={() => setSelected(i)}
              className={`shrink-0 w-20 h-16 rounded overflow-hidden border-2 transition-colors ${
                i === selected ? "border-brand-orange" : "border-transparent opacity-50 hover:opacity-80"
              }`}
            >
              <img src={s.image} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
