"use client"

import { useState } from "react"
import { Button } from "@/components/ui/Button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { FileText, Download, Loader2 } from "lucide-react"

interface Props {
  sessionId: string
}

export default function ComputerUseExportButton({ sessionId }: Props) {
  const [loading, setLoading] = useState<string | null>(null)

  const exportSession = async (format: string) => {
    setLoading(format)
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const res = await fetch(`/api/v1/computer-use/sessions/${sessionId}/export`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ format, include_screenshots: true }),
      })
      if (!res.ok) throw new Error("Export failed")

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `session_${sessionId}.${format === "pdf" ? "pdf" : format === "csv" ? "csv" : "json"}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      console.error("Export error:", e)
      alert("Error al exportar la sesión")
    } finally {
      setLoading(null)
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <FileText className="w-4 h-4" />
          Exportar
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => exportSession("pdf")} disabled={!!loading}>
          {loading === "pdf" ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
          Exportar PDF
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => exportSession("csv")} disabled={!!loading}>
          {loading === "csv" ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
          Exportar CSV
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => exportSession("json")} disabled={!!loading}>
          {loading === "json" ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
          Exportar JSON
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
