"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { Monitor, Pause, Play, Square, Eye } from "lucide-react"

interface ActiveSession {
  id: string
  task_description: string
  status: string
  current_url?: string
  total_steps: number
  browser_type: string
  created_at: string
}

interface Props {
  onConnect: (sessionId: string) => void
}

export default function ComputerUseActiveGrid({ onConnect }: Props) {
  const [sessions, setSessions] = useState<ActiveSession[]>([])
  const [loading, setLoading] = useState(false)

  const fetchActive = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const res = await fetch("/api/v1/computer-use/active-sessions", {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setSessions(data.items || [])
      }
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    fetchActive()
    const interval = setInterval(fetchActive, 5000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running": return "bg-green-500"
      case "paused": return "bg-yellow-500"
      case "pending": return "bg-blue-500"
      default: return "bg-gray-500"
    }
  }

  const getBrowserIcon = (type: string) => {
    switch (type) {
      case "firefox": return "🦊"
      case "webkit": return "🧭"
      default: return "🌐"
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium flex items-center gap-2">
          <Monitor className="w-4 h-4" />
          Sesiones Activas ({sessions.length})
        </h3>
        <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={fetchActive}>
          Actualizar
        </Button>
      </div>

      {sessions.length === 0 ? (
        <p className="text-gray-400 text-sm text-center py-6">No hay sesiones activas</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {sessions.map(session => (
            <div
              key={session.id}
              className="border rounded-lg p-3 bg-white hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => onConnect(session.id)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{getBrowserIcon(session.browser_type)}</span>
                  <Badge variant="outline" className="text-[10px]">
                    {session.browser_type}
                  </Badge>
                </div>
                <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor(session.status)} animate-pulse`} />
              </div>
              <p className="text-sm font-medium truncate mb-1">{session.task_description}</p>
              {session.current_url && (
                <p className="text-xs text-gray-500 truncate mb-2">{session.current_url}</p>
              )}
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>{session.total_steps} pasos</span>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Eye className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
