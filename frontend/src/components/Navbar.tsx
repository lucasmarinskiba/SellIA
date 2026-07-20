'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { LogOut, User, Bell, Menu } from 'lucide-react'
import { alertsApi } from '@/lib/alerts'
import Link from 'next/link'
import { ThemeToggle } from './theme-toggle'
import { ZenModeToggle } from './gamification/ZenModeToggle'

interface NavbarProps {
  onMenuClick?: () => void
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const { user, logout } = useAuth()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    const fetchUnread = async () => {
      try {
        // Try to get unread count from the first business
        // In a real app we'd know the active business, but for now we skip if no business
        // The unread count will show when on alertas/recomendaciones pages
      } catch (e) {
        // silent
      }
    }
    fetchUnread()
    const interval = setInterval(fetchUnread, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="h-16 bg-card/80 backdrop-blur-xl border-b border-border flex items-center justify-between px-4 lg:px-8 sticky top-0 z-30">
      {/* Left: Menu button + Title */}
      <div className="flex items-center gap-3">
        <button 
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-xl hover:bg-accent text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h2 className="text-sm lg:text-lg font-semibold text-foreground/90">Panel de Control</h2>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2 lg:gap-4">
        <ZenModeToggle />
        <ThemeToggle />
        
        <Link 
          href="/dashboard/alertas" 
          className="relative p-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Alertas"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full" aria-hidden="true" />
          )}
        </Link>
        
        <div className="h-6 w-px bg-border hidden sm:block" />
        
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-brand-orange to-brand-violet rounded-xl flex items-center justify-center text-white text-sm font-bold">
            {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-foreground/80">{user?.full_name || 'Usuario'}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
        </div>
        
        <button
          onClick={logout}
          className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          title="Cerrar sesión"
          aria-label="Cerrar sesión"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  )
}
