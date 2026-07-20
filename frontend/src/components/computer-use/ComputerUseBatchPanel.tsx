"use client"

import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Textarea } from "@/components/ui/Textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Loader2, Plus, Trash2, Play, List } from "lucide-react"

interface BatchJob {
  id: string
  name: string
  task_description: string
  urls: string[]
  status: string
  completed_count: number
  failed_count: number
  total_count: number
}

export default function ComputerUseBatchPanel() {
  const [jobs, setJobs] = useState<BatchJob[]>([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState("")
  const [task, setTask] = useState("")
  const [urlsText, setUrlsText] = useState("")

  const createBatchJob = async () => {
    const urls = urlsText.split("\n").map(u => u.trim()).filter(Boolean)
    if (!name || !task || urls.length === 0) return

    setLoading(true)
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const res = await fetch("/api/v1/computer-use/batch-jobs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, task_description: task, urls }),
      })
      if (!res.ok) throw new Error("Failed to create batch job")
      const job = await res.json()
      setJobs(prev => [job, ...prev])
      setShowForm(false)
      setName("")
      setTask("")
      setUrlsText("")
    } catch (e) {
      console.error(e)
      alert("Error al crear el batch job")
    } finally {
      setLoading(false)
    }
  }

  const fetchJobs = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const res = await fetch("/api/v1/computer-use/batch-jobs", {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) setJobs(await res.json())
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <List className="w-4 h-4" />
          Batch Jobs
        </CardTitle>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={fetchJobs}>
            <List className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowForm(!showForm)}>
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {showForm && (
          <div className="space-y-3 mb-4 p-3 bg-gray-50 rounded-lg">
            <Input
              placeholder="Nombre del job"
              value={name}
              onChange={e => setName(e.target.value)}
              className="text-sm"
            />
            <Textarea
              placeholder="Descripción de la tarea"
              value={task}
              onChange={e => setTask(e.target.value)}
              className="text-sm min-h-[60px]"
            />
            <Textarea
              placeholder="URLs (una por línea)"
              value={urlsText}
              onChange={e => setUrlsText(e.target.value)}
              className="text-sm min-h-[80px]"
            />
            <Button onClick={createBatchJob} disabled={loading} size="sm" className="w-full">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 mr-1" />}
              Crear Batch Job
            </Button>
          </div>
        )}

        <div className="space-y-2">
          {jobs.map(job => (
            <div key={job.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm">
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{job.name}</p>
                <p className="text-gray-500 text-xs truncate">{job.task_description}</p>
              </div>
              <div className="flex items-center gap-2 ml-2">
                <Badge variant={job.status === "completed" ? "default" : job.status === "running" ? "secondary" : "outline"}>
                  {job.status}
                </Badge>
                <span className="text-xs text-gray-500">
                  {job.completed_count}/{job.total_count}
                </span>
              </div>
            </div>
          ))}
          {jobs.length === 0 && (
            <p className="text-gray-400 text-sm text-center py-4">No hay batch jobs</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
