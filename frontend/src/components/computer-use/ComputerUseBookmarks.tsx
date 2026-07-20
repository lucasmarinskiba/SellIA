"use client"

import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Bookmark, BookmarkPlus, X } from "lucide-react"

interface BookmarkItem {
  step: number
  label: string
  timestamp: string
}

interface Props {
  bookmarks: BookmarkItem[]
  currentStep: number
  onAddBookmark: (label: string) => void
  onGoToBookmark: (step: number) => void
}

export default function ComputerUseBookmarks({ bookmarks, currentStep, onAddBookmark, onGoToBookmark }: Props) {
  const [isAdding, setIsAdding] = useState(false)
  const [label, setLabel] = useState("")

  const handleAdd = () => {
    if (label.trim()) {
      onAddBookmark(label.trim())
      setLabel("")
      setIsAdding(false)
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-medium text-white/50 uppercase tracking-wider flex items-center gap-1">
          <Bookmark className="w-3 h-3" />
          Bookmarks ({bookmarks.length})
        </h4>
        <Button variant="ghost" size="sm" className="h-5 px-1.5 text-xs" onClick={() => setIsAdding(!isAdding)}>
          {isAdding ? <X className="w-3 h-3" /> : <BookmarkPlus className="w-3 h-3" />}
        </Button>
      </div>

      {isAdding && (
        <div className="flex gap-1">
          <input
            value={label}
            onChange={e => setLabel(e.target.value)}
            placeholder="Etiqueta..."
            className="flex-1 bg-white/5 border border-white/[0.08] rounded px-2 py-1 text-xs text-white placeholder:text-white/20"
            onKeyDown={e => e.key === "Enter" && handleAdd()}
          />
          <Button size="sm" className="h-6 text-[10px] px-2" onClick={handleAdd}>Add</Button>
        </div>
      )}

      <div className="space-y-1">
        {bookmarks.map(bm => (
          <button
            key={bm.step}
            onClick={() => onGoToBookmark(bm.step)}
            className={`w-full flex items-center gap-2 px-2 py-1 rounded text-xs transition-colors ${
              currentStep === bm.step
                ? "bg-brand-orange/20 text-brand-orange"
                : "bg-white/5 text-white/50 hover:bg-white/[0.08] hover:text-white/70"
            }`}
          >
            <Bookmark className="w-3 h-3" />
            <span className="flex-1 text-left truncate">{bm.label}</span>
            <span className="text-white/20 text-[10px]">#{bm.step}</span>
          </button>
        ))}
        {bookmarks.length === 0 && !isAdding && (
          <p className="text-white/20 text-[10px] text-center py-2">Sin bookmarks</p>
        )}
      </div>
    </div>
  )
}
