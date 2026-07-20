import { useEffect, useCallback } from "react"

interface ShortcutHandlers {
  onPause?: () => void
  onResume?: () => void
  onStop?: () => void
  onScreenshot?: () => void
  onFullscreen?: () => void
  onToggleHistory?: () => void
  onToggleChat?: () => void
}

export function useComputerUseKeyboardShortcuts(handlers: ShortcutHandlers, enabled: boolean = true) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return

      // Ignore if typing in input/textarea
      const target = e.target as HTMLElement
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
        return
      }

      switch (e.key.toLowerCase()) {
        case "p":
          e.preventDefault()
          handlers.onPause?.()
          break
        case "r":
          e.preventDefault()
          handlers.onResume?.()
          break
        case "s":
          if (e.shiftKey) {
            e.preventDefault()
            handlers.onStop?.()
          }
          break
        case "c":
          if (e.shiftKey) {
            e.preventDefault()
            handlers.onScreenshot?.()
          }
          break
        case "f":
          if (e.shiftKey) {
            e.preventDefault()
            handlers.onFullscreen?.()
          }
          break
        case "h":
          if (e.shiftKey) {
            e.preventDefault()
            handlers.onToggleHistory?.()
          }
          break
        case "m":
          if (e.shiftKey) {
            e.preventDefault()
            handlers.onToggleChat?.()
          }
          break
      }
    },
    [handlers, enabled]
  )

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])
}
