'use client'

import { useEffect, useState } from 'react'
import { Users, Plus, Trash2, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/Card'

interface TeamMember {
  id: string
  name: string
  email: string
  role: string
  status: string
  joined_at: string
}

interface Assignment {
  id: string
  agent: string
  workload: number
  assigned_at: string
  is_primary: boolean
}

interface MemberPerformance {
  member_id: string
  member_name: string
  assigned_agents: string[]
  metrics: {
    tasks_completed: number
    success_rate: string
    avg_response_time: string
    revenue_generated: string
    lead_conversions: number
    customer_satisfaction: string
  }
  scores: {
    workload: string
    efficiency: string
  }
}

interface TeamMetrics {
  team: {
    total_members: number
    active_members: number
    total_agents_assigned: number
  }
  performance: {
    avg_efficiency: string
    total_revenue: string
    avg_response_time: string
  }
  top_performer: {
    member_id: string
    revenue: string
  }
}

export default function TeamManager({ userId }: { userId: string }) {
  const [members, setMembers] = useState<TeamMember[]>([])
  const [metrics, setMetrics] = useState<TeamMetrics | null>(null)
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null)
  const [memberPerformance, setMemberPerformance] = useState<MemberPerformance | null>(null)
  const [memberAssignments, setMemberAssignments] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddMember, setShowAddMember] = useState(false)
  const [newMemberName, setNewMemberName] = useState('')
  const [newMemberEmail, setNewMemberEmail] = useState('')

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchTeamData()
  }, [userId])

  const fetchTeamData = async () => {
    try {
      setLoading(true)

      const [membersRes, metricsRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/teams/members/${userId}`),
        fetch(`${apiUrl}/api/v1/teams/metrics/${userId}`),
      ])

      if (membersRes.ok) {
        const data = await membersRes.json()
        setMembers(data.members || [])
      }

      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics(data)
      }
    } catch (error) {
      console.error('Team data fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchMemberDetails = async (memberId: string) => {
    try {
      const [perfRes, assignRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/teams/performance/${userId}/${memberId}`),
        fetch(`${apiUrl}/api/v1/teams/assignments/${userId}/${memberId}`),
      ])

      if (perfRes.ok) {
        const data = await perfRes.json()
        setMemberPerformance(data)
      }

      if (assignRes.ok) {
        const data = await assignRes.json()
        setMemberAssignments(data.assignments || [])
      }
    } catch (error) {
      console.error('Member details fetch error:', error)
    }
  }

  const handleSelectMember = (member: TeamMember) => {
    setSelectedMember(member)
    fetchMemberDetails(member.id)
  }

  const handleAddMember = async () => {
    if (!newMemberName || !newMemberEmail) return

    try {
      const res = await fetch(`${apiUrl}/api/v1/teams/members/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          name: newMemberName,
          email: newMemberEmail,
          role: 'agent',
        }),
      })

      if (res.ok) {
        setNewMemberName('')
        setNewMemberEmail('')
        setShowAddMember(false)
        fetchTeamData()
      }
    } catch (error) {
      console.error('Add member error:', error)
    }
  }

  const handleAssignAgent = async (memberId: string, agentType: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/teams/assign-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          member_id: memberId,
          agent_type: agentType,
          workload_percentage: 100,
        }),
      })

      if (res.ok) {
        if (selectedMember) {
          fetchMemberDetails(selectedMember.id)
        }
      }
    } catch (error) {
      console.error('Assign agent error:', error)
    }
  }

  const handleRebalance = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/teams/rebalance/${userId}`, {
        method: 'POST',
      })

      if (res.ok) {
        fetchTeamData()
        if (selectedMember) {
          fetchMemberDetails(selectedMember.id)
        }
      }
    } catch (error) {
      console.error('Rebalance error:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-brand-night flex items-center gap-2">
            <Users className="w-6 h-6" />
            Team Management
          </h2>
          <p className="text-sm text-slate-600 mt-1">Manage team members and agent assignments</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRebalance}
            className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-100 text-sm font-medium"
          >
            Rebalance Workload
          </button>
          <button
            onClick={() => setShowAddMember(true)}
            className="px-4 py-2 bg-brand-orange text-white rounded-lg hover:bg-orange-600 text-sm font-medium flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Member
          </button>
        </div>
      </div>

      {/* Add Member Modal */}
      {showAddMember && (
        <Card className="p-6 border-2 border-brand-orange">
          <h3 className="font-semibold text-brand-night mb-4">Add Team Member</h3>
          <div className="space-y-3">
            <input
              type="text"
              value={newMemberName}
              onChange={(e) => setNewMemberName(e.target.value)}
              placeholder="Full name"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange"
            />
            <input
              type="email"
              value={newMemberEmail}
              onChange={(e) => setNewMemberEmail(e.target.value)}
              placeholder="Email address"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange"
            />
            <div className="flex gap-2">
              <button
                onClick={handleAddMember}
                className="px-4 py-2 bg-brand-orange text-white rounded-lg hover:bg-orange-600 text-sm font-medium"
              >
                Add
              </button>
              <button
                onClick={() => setShowAddMember(false)}
                className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </Card>
      )}

      {/* Metrics Summary */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-6">
            <p className="text-sm text-slate-600 mb-2">Team Members</p>
            <p className="text-3xl font-bold text-brand-night">{metrics.team.total_members}</p>
            <p className="text-xs text-slate-500 mt-2">{metrics.team.active_members} active</p>
          </Card>

          <Card className="p-6">
            <p className="text-sm text-slate-600 mb-2">Total Revenue</p>
            <p className="text-3xl font-bold text-green-600">{metrics.performance.total_revenue}</p>
            <p className="text-xs text-slate-500 mt-2">Team generated</p>
          </Card>

          <Card className="p-6">
            <p className="text-sm text-slate-600 mb-2">Avg Efficiency</p>
            <p className="text-3xl font-bold text-blue-600">{metrics.performance.avg_efficiency}</p>
            <p className="text-xs text-slate-500 mt-2">Across team</p>
          </Card>
        </div>
      )}

      {/* Team Members & Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Members List */}
        <Card className="p-4">
          <h3 className="font-semibold text-brand-night mb-4">Team Members</h3>
          {loading ? (
            <div className="text-center py-8 text-slate-500">Loading...</div>
          ) : members.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm">No members yet</div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {members.map((member) => (
                <button
                  key={member.id}
                  onClick={() => handleSelectMember(member)}
                  className={`w-full p-3 text-left rounded-lg transition-colors ${
                    selectedMember?.id === member.id
                      ? 'bg-orange-100 border border-brand-orange'
                      : 'bg-slate-100 hover:bg-slate-200'
                  }`}
                >
                  <p className="font-medium text-sm text-brand-night">{member.name}</p>
                  <p className="text-xs text-slate-600 mt-1">{member.email}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs ${
                        member.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {member.role}
                    </span>
                  </p>
                </button>
              ))}
            </div>
          )}
        </Card>

        {/* Member Details */}
        {selectedMember && memberPerformance && (
          <Card className="lg:col-span-2 p-6">
            <h3 className="text-xl font-bold text-brand-night mb-4">{selectedMember.name}</h3>

            {/* Assigned Agents */}
            <div className="mb-6">
              <h4 className="font-semibold text-sm text-slate-700 mb-3">Assigned Agents</h4>
              <div className="space-y-2">
                {memberAssignments.map((assign) => (
                  <div key={assign.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-brand-night">{assign.agent}</p>
                      <p className="text-xs text-slate-600">Workload: {assign.workload}%</p>
                    </div>
                    {assign.is_primary && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-medium">
                        Primary
                      </span>
                    )}
                  </div>
                ))}

                {memberAssignments.length === 0 && (
                  <p className="text-sm text-slate-500">No agents assigned</p>
                )}
              </div>

              <div className="mt-3 pt-3 border-t flex gap-2 flex-wrap">
                {['lead_scout', 'closer_bot', 'coach_agent', 'analytics_engine'].map((agent) => {
                  const isAssigned = memberAssignments.some((a) => a.agent === agent)
                  return (
                    <button
                      key={agent}
                      onClick={() => !isAssigned && handleAssignAgent(selectedMember.id, agent)}
                      disabled={isAssigned}
                      className={`text-xs px-2 py-1 rounded ${
                        isAssigned
                          ? 'bg-slate-100 text-slate-500 cursor-default'
                          : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                      }`}
                    >
                      + {agent}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-xs text-slate-600">Success Rate</p>
                <p className="text-lg font-bold text-green-700">{memberPerformance.metrics.success_rate}</p>
              </div>

              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-slate-600">Efficiency</p>
                <p className="text-lg font-bold text-blue-700">{memberPerformance.scores.efficiency}</p>
              </div>

              <div className="p-3 bg-orange-50 rounded-lg">
                <p className="text-xs text-slate-600">Revenue</p>
                <p className="text-lg font-bold text-orange-700">{memberPerformance.metrics.revenue_generated}</p>
              </div>

              <div className="p-3 bg-purple-50 rounded-lg">
                <p className="text-xs text-slate-600">Conversions</p>
                <p className="text-lg font-bold text-purple-700">{memberPerformance.metrics.lead_conversions}</p>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t text-xs text-slate-600">
              <p>Avg Response: {memberPerformance.metrics.avg_response_time}</p>
              <p>Customer Satisfaction: {memberPerformance.metrics.customer_satisfaction}</p>
              <p>Tasks Completed: {memberPerformance.metrics.tasks_completed}</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
