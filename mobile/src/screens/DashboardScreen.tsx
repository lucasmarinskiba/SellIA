import { useEffect, useState } from 'react'
import { View, ScrollView, StyleSheet, Text, RefreshControl } from 'react-native'
import { useAuth } from '@/hooks/useAuth'
import { apiClient } from '@/services/apiClient'

interface DashboardMetrics {
  total_pipeline: number
  deals_this_month: number
  avg_deal_value: number
  close_rate: number
  revenue_forecast: number
}

export default function DashboardScreen() {
  const { user } = useAuth()
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchDashboard = async () => {
    if (!user) return
    setLoading(true)
    try {
      const response = await apiClient.getDashboard(user.id)
      setMetrics(response.data)
    } catch (error) {
      console.error('Fetch dashboard error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [user])

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchDashboard} />}
    >
      <View style={styles.header}>
        <Text style={styles.greeting}>Hello, {user?.name}! 👋</Text>
        <Text style={styles.subtitle}>Your sales metrics at a glance</Text>
      </View>

      {metrics && (
        <View style={styles.metricsGrid}>
          <View style={styles.metric}>
            <Text style={styles.metricValue}>${(metrics.total_pipeline / 1000).toFixed(1)}k</Text>
            <Text style={styles.metricLabel}>Pipeline</Text>
          </View>

          <View style={styles.metric}>
            <Text style={styles.metricValue}>{metrics.deals_this_month}</Text>
            <Text style={styles.metricLabel}>Deals</Text>
          </View>

          <View style={styles.metric}>
            <Text style={styles.metricValue}>${(metrics.avg_deal_value / 1000).toFixed(1)}k</Text>
            <Text style={styles.metricLabel}>Avg Deal</Text>
          </View>

          <View style={styles.metric}>
            <Text style={styles.metricValue}>{(metrics.close_rate * 100).toFixed(1)}%</Text>
            <Text style={styles.metricLabel}>Close Rate</Text>
          </View>

          <View style={[styles.metric, styles.metricFullWidth]}>
            <Text style={styles.metricValue}>${(metrics.revenue_forecast / 1000).toFixed(1)}k</Text>
            <Text style={styles.metricLabel}>Revenue Forecast</Text>
          </View>
        </View>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  header: {
    marginBottom: 24,
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  metric: {
    width: '48%',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  metricFullWidth: {
    width: '100%',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FF8C00',
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 12,
    color: '#999',
    textTransform: 'uppercase',
  },
})
