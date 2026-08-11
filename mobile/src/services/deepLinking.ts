import { useEffect } from 'react'
import * as Linking from 'expo-linking'
import { useRouter } from 'expo-router'

interface DeepLinkPayload {
  type: 'approval' | 'deal' | 'comment' | 'notification'
  id: string
  data?: Record<string, unknown>
}

const prefix = Linking.createURL('/')

export const linking = {
  prefixes: [prefix, 'sellia://', 'https://sellia.com'],
  config: {
    screens: {
      '(tabs)': {
        screens: {
          index: 'dashboard',
          pipeline: 'pipeline',
          pipeline_detail: 'pipeline/:dealId',
          approvals: 'approvals/:actionId',
          notifications: 'notifications/:notificationId',
          profile: 'profile',
        },
      },
      '(auth)': {
        screens: {
          login: 'login',
          register: 'register',
        },
      },
      notFound: '*',
    },
  },
}

export const useDeepLinking = () => {
  const router = useRouter()

  useEffect(() => {
    const handleDeepLink = ({ url }: { url: string }) => {
      const route = url.replace(/.*?:\/\/?/, '')
      const routeName = route.split('/')[0]
      const params = route.split('/').slice(1)

      if (routeName === 'approvals' && params[0]) {
        router.push(`/(tabs)/approvals?actionId=${params[0]}`)
      } else if (routeName === 'pipeline' && params[0]) {
        router.push(`/(tabs)/pipeline/${params[0]}`)
      } else if (routeName === 'notifications' && params[0]) {
        router.push(`/(tabs)/notifications?id=${params[0]}`)
      } else if (routeName === 'dashboard') {
        router.push('/(tabs)/')
      }
    }

    const subscription = Linking.addEventListener('url', handleDeepLink)

    Linking.getInitialURL().then((url) => {
      if (url != null) {
        handleDeepLink({ url })
      }
    })

    return () => subscription.remove()
  }, [router])
}

export const createDeepLink = (payload: DeepLinkPayload): string => {
  const { type, id, data } = payload
  const base = 'sellia://'

  const params = new URLSearchParams()
  if (data) {
    Object.entries(data).forEach(([key, value]) => {
      params.append(key, String(value))
    })
  }

  const queryString = params.toString() ? `?${params.toString()}` : ''

  switch (type) {
    case 'approval':
      return `${base}approvals/${id}${queryString}`
    case 'deal':
      return `${base}pipeline/${id}${queryString}`
    case 'comment':
      return `${base}pipeline/${id}/comments${queryString}`
    case 'notification':
      return `${base}notifications/${id}${queryString}`
    default:
      return `${base}dashboard`
  }
}
