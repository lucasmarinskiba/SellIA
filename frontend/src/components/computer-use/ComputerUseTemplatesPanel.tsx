"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { ScrollText, Plus, Play, Search } from "lucide-react"

interface Template {
  id: string
  name: string
  description?: string
  task_description: string
  start_url?: string
  tags: string[]
  usage_count: number
}

interface Props {
  onSelectTemplate: (template: { task_description: string; start_url?: string }) => void
}

export default function ComputerUseTemplatesPanel({ onSelectTemplate }: Props) {
  const [templates, setTemplates] = useState<Template[]>([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(false)

  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const res = await fetch(`/api/v1/computer-use/templates?search=${encodeURIComponent(search)}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setTemplates(data.items || [])
      }
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    fetchTemplates()
  }, [search])

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <ScrollText className="w-4 h-4" />
          Plantillas
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative mb-3">
          <Search className="absolute left-2.5 top-2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Buscar plantillas..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-8 text-sm h-8"
          />
        </div>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {templates.map(t => (
            <div
              key={t.id}
              className="group flex items-start justify-between p-2.5 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
              onClick={() => onSelectTemplate({ task_description: t.task_description, start_url: t.start_url })}
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{t.name}</p>
                {t.description && <p className="text-gray-500 text-xs truncate">{t.description}</p>}
                <div className="flex items-center gap-1 mt-1 flex-wrap">
                  {t.tags.map(tag => (
                    <Badge key={tag} variant="secondary" className="text-[10px] px-1 py-0">{tag}</Badge>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Play className="w-3 h-3" />
                </Button>
              </div>
            </div>
          ))}
          {templates.length === 0 && (
            <p className="text-gray-400 text-sm text-center py-4">No hay plantillas</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
