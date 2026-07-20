"use client"

import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Textarea } from "@/components/ui/Textarea"
import { MessageCircle, X, Pin } from "lucide-react"

interface Annotation {
  id: string
  step_number: number
  content: string
  x_coordinate?: number
  y_coordinate?: number
  color: string
}

interface Props {
  sessionId: string
  stepNumber: number
  annotations: Annotation[]
  onAnnotationAdded: (ann: Annotation) => void
}

export default function ComputerUseAnnotationsOverlay({ sessionId, stepNumber, annotations, onAnnotationAdded }: Props) {
  const [isAdding, setIsAdding] = useState(false)
  const [content, setContent] = useState("")
  const [selectedColor, setSelectedColor] = useState("#f59e0b")

  const stepAnnotations = annotations.filter(a => a.step_number === stepNumber)

  const addAnnotation = async () => {
    if (!content.trim()) return
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const res = await fetch(`/api/v1/computer-use/sessions/${sessionId}/annotations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          step_number: stepNumber,
          content: content.trim(),
          color: selectedColor,
        }),
      })
      if (!res.ok) throw new Error("Failed")
      const ann = await res.json()
      onAnnotationAdded(ann)
      setContent("")
      setIsAdding(false)
    } catch (e) {
      console.error(e)
      alert("Error al agregar anotación")
    }
  }

  const colors = ["#f59e0b", "#ef4444", "#3b82f6", "#10b981", "#8b5cf6", "#ec4899"]

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium flex items-center gap-1">
          <MessageCircle className="w-3.5 h-3.5" />
          Anotaciones ({stepAnnotations.length})
        </h4>
        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={() => setIsAdding(!isAdding)}>
          {isAdding ? <X className="w-3 h-3" /> : <Pin className="w-3 h-3" />}
          {isAdding ? "Cancelar" : "Agregar"}
        </Button>
      </div>

      {isAdding && (
        <div className="space-y-2 p-2 bg-gray-50 rounded-lg">
          <Textarea
            placeholder="Escribe tu anotación..."
            value={content}
            onChange={e => setContent(e.target.value)}
            className="text-sm min-h-[60px]"
          />
          <div className="flex items-center gap-2">
            {colors.map(c => (
              <button
                key={c}
                onClick={() => setSelectedColor(c)}
                className={`w-6 h-6 rounded-full border-2 ${selectedColor === c ? "border-gray-900 scale-110" : "border-transparent"}`}
                style={{ backgroundColor: c }}
              />
            ))}
            <Button size="sm" className="ml-auto h-7 text-xs" onClick={addAnnotation}>
              Guardar
            </Button>
          </div>
        </div>
      )}

      <div className="space-y-1.5 max-h-40 overflow-y-auto">
        {stepAnnotations.map(ann => (
          <div
            key={ann.id}
            className="flex items-start gap-2 p-2 rounded-md text-xs"
            style={{ backgroundColor: `${ann.color}15`, borderLeft: `3px solid ${ann.color}` }}
          >
            <span className="text-gray-700 flex-1">{ann.content}</span>
          </div>
        ))}
        {stepAnnotations.length === 0 && !isAdding && (
          <p className="text-gray-400 text-xs text-center py-2">Sin anotaciones en este paso</p>
        )}
      </div>
    </div>
  )
}
