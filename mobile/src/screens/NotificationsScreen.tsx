import { useEffect } from 'react'
import { View, ScrollView, StyleSheet, Text, TouchableOpacity, RefreshControl } from 'react-native'
import { useAuth } from '@/hooks/useAuth'
import { useNotifications } from '@/hooks/useNotifications'

export default function NotificationsScreen() {
  const { user } = useAuth()
  const { notifications, isLoading, unreadCount, fetchNotifications, markAsRead } =
    useNotifications()

  useEffect(() => {
    if (user) {
      fetchNotifications(user.id)
    }
  }, [user])

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'approval':
        return '#FF8C00'
      case 'deal_update':
        return '#4CAF50'
      case 'comment':
        return '#2196F3'
      case 'mention':
        return '#9C27B0'
      default:
        return '#999'
    }
  }

  const getTypeLabel = (type: string) => {
    return type.replace(/_/g, ' ').toUpperCase()
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={isLoading}
          onRefresh={() => user && fetchNotifications(user.id)}
        />
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>Notifications</Text>
        {unreadCount > 0 && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{unreadCount}</Text>
          </View>
        )}
      </View>

      {notifications.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>All caught up! ✨</Text>
          <Text style={styles.emptySubtext}>No notifications</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {notifications.map((notification) => (
            <TouchableOpacity
              key={notification.id}
              style={[styles.card, !notification.read && styles.cardUnread]}
              onPress={() => markAsRead(notification.id)}
            >
              <View style={styles.cardTop}>
                <View
                  style={[
                    styles.typeIndicator,
                    { backgroundColor: getTypeColor(notification.type) },
                  ]}
                />
                <View style={styles.cardContent}>
                  <Text style={styles.title}>{notification.title}</Text>
                  <Text style={styles.message}>{notification.message}</Text>
                </View>
              </View>

              <View style={styles.cardBottom}>
                <Text style={styles.typeLabel}>{getTypeLabel(notification.type)}</Text>
                <Text style={styles.timestamp}>
                  {new Date(notification.timestamp).toLocaleString()}
                </Text>
              </View>

              {!notification.read && <View style={styles.unreadDot} />}
            </TouchableOpacity>
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
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  cardUnread: {
    backgroundColor: '#fafafa',
    borderLeftWidth: 4,
    borderLeftColor: '#FF8C00',
  },
  cardTop: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  typeIndicator: {
    width: 4,
    borderRadius: 2,
    marginRight: 12,
  },
  cardContent: {
    flex: 1,
  },
  message: {
    fontSize: 13,
    color: '#666',
    marginTop: 4,
  },
  cardBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
  },
  typeLabel: {
    fontSize: 10,
    color: '#999',
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  timestamp: {
    fontSize: 10,
    color: '#999',
  },
  unreadDot: {
    position: 'absolute',
    top: 16,
    right: 16,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF8C00',
  },
})
