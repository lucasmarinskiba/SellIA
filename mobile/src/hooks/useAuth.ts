import { create } from 'zustand'
import { apiClient } from '@/services/apiClient'
import * as SecureStore from 'expo-secure-store'

interface User {
  id: string
  email: string
  name: string
  role: string
}

interface AuthState {
  user: User | null
  isLoading: boolean
  isSignedIn: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, name: string) => Promise<void>
  signOut: () => Promise<void>
  restoreToken: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isSignedIn: false,

  signIn: async (email: string, password: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (response.ok) {
        const data = await response.json()
        await apiClient.setToken(data.access_token)
        await SecureStore.setItemAsync('auth_token', data.access_token)

        const userResponse = await apiClient.getCurrentUser()
        set({
          user: userResponse.data,
          isSignedIn: true,
        })
      }
    } catch (error) {
      console.error('Sign in error:', error)
      throw error
    }
  },

  signUp: async (email: string, password: string, name: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      })

      if (response.ok) {
        const data = await response.json()
        await apiClient.setToken(data.access_token)
        await SecureStore.setItemAsync('auth_token', data.access_token)

        const userResponse = await apiClient.getCurrentUser()
        set({
          user: userResponse.data,
          isSignedIn: true,
        })
      }
    } catch (error) {
      console.error('Sign up error:', error)
      throw error
    }
  },

  signOut: async () => {
    await apiClient.clearAuth()
    set({
      user: null,
      isSignedIn: false,
    })
  },

  restoreToken: async () => {
    try {
      const token = await SecureStore.getItemAsync('auth_token')
      if (token) {
        await apiClient.setToken(token)
        const userResponse = await apiClient.getCurrentUser()
        set({
          user: userResponse.data,
          isSignedIn: true,
        })
      }
    } catch (error) {
      console.error('Restore token error:', error)
      await apiClient.clearAuth()
    } finally {
      set({ isLoading: false })
    }
  },
}))

export const useAuth = () => useAuthStore()
