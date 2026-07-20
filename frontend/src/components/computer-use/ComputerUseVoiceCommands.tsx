"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { Mic, MicOff } from "lucide-react"

interface Props {
  onCommand: (command: string) => void
  disabled?: boolean
}

export default function ComputerUseVoiceCommands({ onCommand, disabled }: Props) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState("")
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    if (typeof window === "undefined") return
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    recognition.lang = "es-ES"
    recognition.continuous = false
    recognition.interimResults = true

    recognition.onstart = () => setIsListening(true)
    recognition.onend = () => setIsListening(false)
    recognition.onresult = (event: any) => {
      const text = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join(" ")
      setTranscript(text)
      if (event.results[0].isFinal) {
        onCommand(text)
        setTranscript("")
      }
    }

    recognitionRef.current = recognition
  }, [onCommand])

  const toggle = useCallback(() => {
    if (!recognitionRef.current) {
      alert("Tu navegador no soporta reconocimiento de voz")
      return
    }
    if (isListening) {
      recognitionRef.current.stop()
    } else {
      recognitionRef.current.start()
    }
  }, [isListening])

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={toggle}
        disabled={disabled}
        className={`p-2 rounded-lg transition-colors ${
          isListening
            ? "bg-red-500/20 text-red-400 animate-pulse"
            : "bg-white/5 text-white/40 hover:bg-white/10 hover:text-white/60"
        }`}
        title={isListening ? "Detener" : "Comando de voz"}
      >
        {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
      </button>
      {transcript && (
        <span className="text-xs text-white/40 truncate max-w-[200px]">{transcript}</span>
      )}
    </div>
  )
}
