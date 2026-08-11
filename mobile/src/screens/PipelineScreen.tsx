import { useEffect } from 'react'
import { View, ScrollView, StyleSheet, Text, TouchableOpacity, RefreshControl } from 'react-native'
import { useAuth } from '@/hooks/useAuth'
import { usePipeline } from '@/hooks/usePipeline'

const STAGES = ['discovery', 'qualified', 'proposal', 'negotiation', 'closed']

export default function PipelineScreen() {
  const { user } = useAuth()
  const { deals, isLoading, fetchDeals, updateDealStage } = usePipeline()

  useEffect(() => {
    if (user) {
      fetchDeals(user.id)
    }
  }, [user])

  const dealsByStage = STAGES.reduce(
    (acc, stage) => {
      acc[stage] = deals.filter((d) => d.stage === stage)
      return acc
    },
    {} as Record<string, typeof deals>
  )

  const handleStageDrop = async (dealId: string, newStage: string) => {
    await updateDealStage(dealId, newStage)
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={() => user && fetchDeals(user.id)} />}
      horizontal
      scrollEventThrottle={16}
    >
      <View style={styles.kanbanBoard}>
        {STAGES.map((stage) => (
          <View key={stage} style={styles.column}>
            <Text style={styles.columnTitle}>{stage.toUpperCase()}</Text>
            <Text style={styles.columnCount}>{dealsByStage[stage].length}</Text>

            <View style={styles.dealList}>
              {dealsByStage[stage].map((deal) => (
                <TouchableOpacity key={deal.id} style={styles.card}>
                  <Text style={styles.dealName}>{deal.name}</Text>
                  <Text style={styles.dealValue}>${(deal.value / 1000).toFixed(1)}k</Text>
                  <Text style={styles.dealCustomer}>{deal.customer}</Text>
                  <View style={styles.probabilityBar}>
                    <View
                      style={[
                        styles.probabilityFill,
                        { width: `${deal.probability}%` },
                      ]}
                    />
                  </View>
                  <Text style={styles.dealMeta}>{deal.days_in_stage}d in stage</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  kanbanBoard: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 12,
    gap: 12,
  },
  column: {
    width: 280,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  columnTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  columnCount: {
    fontSize: 12,
    color: '#999',
    marginBottom: 12,
  },
  dealList: {
    gap: 8,
  },
  card: {
    backgroundColor: '#fafafa',
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#FF8C00',
  },
  dealName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  dealValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FF8C00',
    marginBottom: 4,
  },
  dealCustomer: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  probabilityBar: {
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    marginBottom: 8,
    overflow: 'hidden',
  },
  probabilityFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  dealMeta: {
    fontSize: 11,
    color: '#999',
  },
})
