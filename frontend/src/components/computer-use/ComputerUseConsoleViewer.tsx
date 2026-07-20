"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/Badge"
import { Terminal, Globe, AlertCircle } from "lucide-react"

interface ConsoleLog {
  level: string
  text: string
  timestamp: string
}

interface NetworkRequest {
  method: string
  url: string
  status?: number
  duration_ms?: number
}

interface Props {
  consoleLogs: ConsoleLog[]
  networkRequests: NetworkRequest[]
}

export default function ComputerUseConsoleViewer({ consoleLogs, networkRequests }: Props) {
  const [tab, setTab] = useState<"console" | "network">("console")

  const getLevelColor = (level: string) => {
    switch (level) {
      case "error": case "pageerror": return "text-red-400"
      case "warn": return "text-yellow-400"
      case "info": return "text-blue-400"
      default: return "text-gray-400"
    }
  }

  return (
    <div className="bg-[#0A0E1A] rounded-xl border border-white/[0.08] overflow-hidden">
      <div className="flex items-center border-b border-white/[0.06]">
        <button
          onClick={() => setTab("console")}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
            tab === "console" ? "text-white border-b-2 border-brand-orange" : "text-white/40 hover:text-white/60"
          }`}
        >
          <Terminal className="w-3 h-3" />
          Console ({consoleLogs.length})
        </button>
        <button
          onClick={() => setTab("network")}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
            tab === "network" ? "text-white border-b-2 border-brand-orange" : "text-white/40 hover:text-white/60"
          }`}
        >
          <Globe className="w-3 h-3" />
          Network ({networkRequests.length})
        </button>
      </div>

      <div className="max-h-48 overflow-y-auto p-2 space-y-1">
        {tab === "console" && (
          <>
            {consoleLogs.map((log, i) => (
              <div key={i} className={`text-xs font-mono break-all ${getLevelColor(log.level)}`}>
                <span className="text-white/20 mr-1">[{log.level}]</span>
                {log.text}
              </div>
            ))}
            {consoleLogs.length === 0 && (
              <p className="text-white/20 text-xs text-center py-4">No console logs</p>
            )}
          </>
        )}
        {tab === "network" && (
          <>
            {networkRequests.map((req, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="text-white/30 font-mono w-8">{req.method}</span>
                <span className={`w-8 text-right ${
                  req.status && req.status >= 400 ? "text-red-400" : "text-green-400"
                }`}>
                  {req.status || "---"}
                </span>
                <span className="text-white/40 truncate flex-1">{req.url}</span>
                {req.duration_ms && (
                  <span className="text-white/20 w-12 text-right">{req.duration_ms.toFixed(0)}ms</span>
                )}
              </div>
            ))}
            {networkRequests.length === 0 && (
              <p className="text-white/20 text-xs text-center py-4">No network requests</p>
            )}
          </>
        )}
      </div>
    </div>
  )
}
