import { View, ScrollView, StyleSheet, Text, TouchableOpacity, Alert } from 'react-native'
import { useAuth } from '@/hooks/useAuth'
import { offlineSync } from '@/services/offlineSync'

export default function ProfileScreen() {
  const { user, signOut } = useAuth()

  const handleSignOut = async () => {
    Alert.alert('Sign Out', 'Are you sure?', [
      { text: 'Cancel', onPress: () => {}, style: 'cancel' },
      {
        text: 'Sign Out',
        onPress: async () => {
          await signOut()
        },
        style: 'destructive',
      },
    ])
  }

  const handleClearCache = async () => {
    Alert.alert('Clear Cache', 'This will clear offline data', [
      { text: 'Cancel', onPress: () => {}, style: 'cancel' },
      {
        text: 'Clear',
        onPress: async () => {
          await offlineSync.clearExpired()
          Alert.alert('Success', 'Cache cleared')
        },
        style: 'destructive',
      },
    ])
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.name?.[0]?.toUpperCase()}</Text>
        </View>

        <Text style={styles.name}>{user?.name}</Text>
        <Text style={styles.email}>{user?.email}</Text>
        <View style={styles.roleBadge}>
          <Text style={styles.roleText}>{user?.role?.toUpperCase()}</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Settings</Text>

        <TouchableOpacity style={styles.setting}>
          <Text style={styles.settingLabel}>Notifications</Text>
          <Text style={styles.settingValue}>Enabled</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.setting}>
          <Text style={styles.settingLabel}>Offline Mode</Text>
          <Text style={styles.settingValue}>Active</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.setting}>
          <Text style={styles.settingLabel}>App Version</Text>
          <Text style={styles.settingValue}>1.0.0</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data</Text>

        <TouchableOpacity style={styles.action} onPress={handleClearCache}>
          <Text style={styles.actionText}>Clear Cache</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.action, styles.actionDanger]} onPress={handleSignOut}>
          <Text style={[styles.actionText, styles.actionTextDanger]}>Sign Out</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  profileCard: {
    backgroundColor: '#fff',
    paddingVertical: 40,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#FF8C00',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  avatarText: {
    color: '#fff',
    fontSize: 32,
    fontWeight: 'bold',
  },
  name: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  email: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  roleBadge: {
    backgroundColor: '#e8f5e9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  roleText: {
    color: '#2e7d32',
    fontSize: 11,
    fontWeight: '600',
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  setting: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 0,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  settingLabel: {
    fontSize: 14,
    color: '#1a1a1a',
  },
  settingValue: {
    fontSize: 12,
    color: '#999',
  },
  action: {
    backgroundColor: '#fff',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  actionDanger: {
    borderColor: '#f44336',
  },
  actionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    textAlign: 'center',
  },
  actionTextDanger: {
    color: '#f44336',
  },
})
