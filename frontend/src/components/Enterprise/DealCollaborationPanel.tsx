'use client'

import { useEffect, useState } from 'react'
import { Send, MessageCircle, Users, Clock } from 'lucide-react'
import { Card } from '@/components/ui/card'

interface Comment {
  id: string
  user_id: string
  content: string
  mentions: string[]
  created_at: string
}

interface Activity {
  type: 'comment' | 'share'
  id: string
  user_id: string
  timestamp: string
  content?: string
  shared_with?: string
}

export default function DealCollaborationPanel({ userId, dealId }: { userId: string; dealId: string }) {
  const [comments, setComments] = useState<Comment[]>([])
  const [activity, setActivity] = useState<Activity[]>([])
  const [newComment, setNewComment] = useState('')
  const [mentions, setMentions] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [teamMembers] = useState(['team_1', 'team_2', 'team_3'])

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchComments()
    connectWebSocket()

    return () => {
      if (ws) ws.close()
    }
  }, [dealId, userId])

  const fetchComments = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/collaboration/comments/${dealId}?limit=50`)
      if (res.ok) {
        const data = await res.json()
        setComments(data.comments || [])
      }

      const actRes = await fetch(`${apiUrl}/api/v1/collaboration/activity/${dealId}`)
      if (actRes.ok) {
        const actData = await actRes.json()
        setActivity(actData.activity || [])
      }
    } catch (error) {
      console.error('Fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const connectWebSocket = () => {
    try {
      const wsUrl = `${apiUrl.replace('http', 'ws')}/ws/deal/${dealId}`
      const socket = new WebSocket(wsUrl)

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'comment_added') {
          fetchComments()
        }
      }

      setWs(socket)
    } catch (error) {
      console.error('WebSocket error:', error)
    }
  }

  const handleAddComment = async () => {
    if (!newComment.trim()) return

    try {
      const res = await fetch(`${apiUrl}/api/v1/collaboration/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          deal_id: dealId,
          content: newComment,
          mentions,
        }),
      })

      if (res.ok) {
        setNewComment('')
        setMentions([])
        fetchComments()

        // Broadcast via WebSocket
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(`comment:${newComment}`)
        }
      }
    } catch (error) {
      console.error('Add comment error:', error)
    }
  }

  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-brand-night flex items-center gap-2">
          <MessageCircle className="w-5 h-5" />
          Team Discussion
        </h3>
        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
          {comments.length} comments
        </span>
      </div>

      {loading ? (
        <Card className="p-6 text-center text-slate-500">Loading discussion...</Card>
      ) : (
        <>
          {/* Activity Feed */}
          <Card className="p-4 max-h-96 overflow-y-auto space-y-3 bg-slate-50">
            {activity.length === 0 ? (
              <p className="text-center text-slate-500 text-sm py-8">No activity yet. Start the conversation!</p>
            ) : (
              activity.map((item) => (
                <div key={item.id} className="p-3 bg-white rounded-lg border border-slate-200">
                  {item.type === 'comment' ? (
                    <>
                      <div className="flex items-start justify-between">
                        <p className="font-medium text-sm text-brand-night">{item.user_id}</p>
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatTime(item.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm text-slate-700 mt-2">{item.content}</p>
                    </>
                  ) : (
                    <p className="text-sm text-slate-600">
                      <span className="font-medium">{item.user_id}</span> shared with{' '}
                      <span className="font-medium">{item.shared_with}</span>
                    </p>
                  )}
                </div>
              ))
            )}
          </Card>

          {/* Comment Input */}
          <Card className="p-4">
            <div className="space-y-3">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add comment... (use @mention for team members)"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange text-sm"
                rows={3}
              />

              {/* @mention suggestions */}
              {newComment.includes('@') && (
                <div className="p-2 bg-slate-50 rounded border border-slate-200 text-sm">
                  <p className="text-xs text-slate-600 mb-2">Mention teammate:</p>
                  <div className="flex gap-2 flex-wrap">
                    {teamMembers
                      .filter((tm) => tm.includes(newComment.split('@').pop() || ''))
                      .map((tm) => (
                        <button
                          key={tm}
                          onClick={() => {
                            setMentions([...mentions, tm])
                            setNewComment(newComment.replace('@' + newComment.split('@').pop(), `@${tm} `))
                          }}
                          className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200"
                        >
                          {tm}
                        </button>
                      ))}
                  </div>
                </div>
              )}

              <button
                onClick={handleAddComment}
                disabled={!newComment.trim()}
                className="w-full px-4 py-2 bg-brand-orange text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
              >
                <Send className="w-4 h-4" />
                Post Comment
              </button>
            </div>
          </Card>

          {/* Shared With */}
          {activity.some((a) => a.type === 'share') && (
            <Card className="p-4">
              <p className="text-sm font-semibold text-brand-night mb-2 flex items-center gap-2">
                <Users className="w-4 h-4" />
                Shared With
              </p>
              <div className="space-y-1">
                {activity
                  .filter((a) => a.type === 'share')
                  .map((share) => (
                    <p key={share.id} className="text-sm text-slate-600">
                      {share.shared_with} (by {share.user_id})
                    </p>
                  ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}

