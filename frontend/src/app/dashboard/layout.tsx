'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import Sidebar from '@/components/Sidebar'
import Navbar from '@/components/Navbar'
import SecurityAlert from '@/components/SecurityAlert'
import SellIAAssistant from '@/components/SellIAAssistant'
import { CelebrationSystem } from '@/components/gamification/CelebrationSystem'
import { ZenModeProvider, ZenOverlay } from '@/components/gamification/ZenModeToggle'
import { MotivationalToast } from '@/components/gamification/MotivationalToast'
import FeedbackWidget from '@/components/FeedbackWidget'
import NpsWidget from '@/components/NpsWidget'
import FomoToast from '@/components/FomoToast'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [loading, user, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center animate-pulse">
              <svg width="28" height="28" viewBox="0 0 100 100" fill="none">
                <path d="M50 15L83.3 34V72L50 91L16.7 72V34L50 15Z" fill="url(#g1)"/>
                <path d="M35 38C35 38 42 32 50 32C58 32 65 38 65 46C65 54 58 60 50 60C47 60 44 59 42 57L35 64L37 54C36 52 35 49 35 46C35 44 35 41 35 38Z" fill="white" fillOpacity="0.9"/>
                <path d="M52 36L48 44H54L48 52" stroke="#FF6B35" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                <defs>
                  <linearGradient id="g1" x1="50" y1="15" x2="50" y2="91">
                    <stop stopColor="#0F2D4A"/>
                    <stop offset="1" stopColor="#0A2540"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div className="absolute inset-0 rounded-2xl bg-primary/20 blur-xl animate-pulse"/>
          </div>
          <p className="text-sm text-muted-foreground">Cargando dashboard...</p>
        </div>
      </div>
    )
  }

  if (!user) return null

  return (
    <ZenModeProvider>
      <div className="min-h-screen flex bg-background">
        {/* Celebration system */}
        <CelebrationSystem />
        <ZenOverlay />
        <MotivationalToast />
        <FeedbackWidget />
        <NpsWidget />
        <FomoToast />

        {/* Mobile overlay */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        
        {/* Sidebar */}
        <div className={`
          fixed lg:static inset-y-0 left-0 z-50 transition-transform duration-300 ease-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}>
          <Sidebar onClose={() => setSidebarOpen(false)} />
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0">
          <Navbar onMenuClick={() => setSidebarOpen(true)} />
          <main className="flex-1 overflow-auto bg-background">
            {children}
          </main>
          <SecurityAlert />
          <SellIAAssistant />
        </div>
      </div>
    </ZenModeProvider>
  )
}
