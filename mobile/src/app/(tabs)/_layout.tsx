import { Tabs } from 'expo-router'
import { View } from 'react-native'
import OfflineIndicator from '@/components/OfflineIndicator'

export default function TabLayout() {
  return (
    <View style={{ flex: 1 }}>
      <OfflineIndicator />
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: '#FF8C00',
          tabBarInactiveTintColor: '#999',
          headerShown: false,
          tabBarStyle: {
            paddingBottom: 8,
            height: 60,
            borderTopWidth: 1,
            borderTopColor: '#e0e0e0',
          },
        }}
      >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarLabel: 'Dashboard',
        }}
      />
      <Tabs.Screen
        name="pipeline"
        options={{
          title: 'Pipeline',
          tabBarLabel: 'Pipeline',
        }}
      />
      <Tabs.Screen
        name="approvals"
        options={{
          title: 'Approvals',
          tabBarLabel: 'Approvals',
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title: 'Notifications',
          tabBarLabel: 'Notifications',
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarLabel: 'Profile',
        }}
      />
    </Tabs>
    </View>
  )
}
