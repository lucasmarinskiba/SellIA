import { useEffect, useState } from 'react'
import { View, ScrollView, StyleSheet, Text, TouchableOpacity, Alert, RefreshControl } from 'react-native'
import { useAuth } from '@/hooks/useAuth'
import { apiClient } from '@/services/apiClient'

interface Approval {
  id: string
  action_id: string
  action_type: string
  requested_by: string
  created_at: string
}

export default function ApprovalsScreen() {
  const { user } = useAuth()
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [loading, setLoading] = useState(false)

  const fetchApprovals = async () => {
    if (!user) return
    setLoading(true)
    try {
      const response = await apiClient.getPendingApprovals(user.id)
      setApprovals(response.data.approvals || [])
    } catch (error) {
      console.error('Fetch approvals error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const interval = setInterval(fetchApprovals, 30000)
    fetchApprovals()
    return () => clearInterval(interval)
  }, [user])

  const handleApprove = async (actionId: string) => {
    if (!user) return
    try {
      await apiClient.approveAction(actionId, user.id, 'approved')
      Alert.alert('Success', 'Action approved')
      fetchApprovals()
    } catch (error) {
      Alert.alert('Error', 'Failed to approve action')
    }
  }

  const handleReject = async (actionId: string) => {
    if (!user) return
    try {
      await apiClient.approveAction(actionId, user.id, 'rejected')
      Alert.alert('Success', 'Action rejected')
      fetchApprovals()
    } catch (error) {
      Alert.alert('Error', 'Failed to reject action')
    }
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchApprovals} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Pending Approvals</Text>
        {approvals.length > 0 && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{approvals.length}</Text>
          </View>
        )}
      </View>

      {approvals.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>All caught up! 🎉</Text>
          <Text style={styles.emptySubtext}>No pending approvals</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {approvals.map((approval) => (
            <View key={approval.id} style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.actionType}>{approval.action_type}</Text>
                <Text style={styles.requestedBy}>by {approval.requested_by}</Text>
              </View>

              <Text style={styles.timestamp}>
                {new Date(approval.created_at).toLocaleString()}
              </Text>

              <View style={styles.actions}>
                <TouchableOpacity
                  style={[styles.button, styles.approveButton]}
                  onPress={() => handleApprove(approval.action_id)}
                >
                  <Text style={styles.buttonText}>Approve</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.button, styles.rejectButton]}
                  onPress={() => handleReject(approval.action_id)}
                >
                  <Text style={styles.buttonText}>Reject</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  badge: {
    backgroundColor: '#FF8C00',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  badgeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
  },
  list: {
    paddingHorizontal: 16,
    gap: 12,
    paddingBottom: 20,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#FF8C00',
  },
  cardHeader: {
    marginBottom: 12,
  },
  actionType: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
    textTransform: 'capitalize',
  },
  requestedBy: {
    fontSize: 12,
    color: '#666',
  },
  timestamp: {
    fontSize: 11,
    color: '#999',
    marginBottom: 12,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  button: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  approveButton: {
    backgroundColor: '#4CAF50',
  },
  rejectButton: {
    backgroundColor: '#f44336',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 12,
  },
})
