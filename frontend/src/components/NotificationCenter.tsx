'use client'

import { useState } from 'react'
import { useNotifications } from '@/hooks/useNotifications'
import { Bell, X, CheckCircle, AlertCircle, Zap, Star } from 'lucide-react'
import Button from './ui/Button'
import { Card } from './ui/card'
import Link from 'next/link'

export default function NotificationCenter() {
  const { notifications, unreadCount, markAsRead, dismissNotification, approveAction, NOTIFICATION_TYPES } = useNotifications()
  const [isOpen, setIsOpen] = useState(false)

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'border-red-200 bg-red-50'
      case 'high':
        return 'border-orange-200 bg-orange-50'
      case 'normal':
        return 'border-slate-200 bg-slate-50'
      default:
        return 'border-blue-200 bg-blue-50'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'agent_alert':
        return <Zap className="w-5 h-5 text-blue-600" />
      case 'sale_celebration':
        return <Star className="w-5 h-5 text-green-600" />
      case 'strategy':
        return <Zap className="w-5 h-5 text-purple-600" />
      case 'action_required':
        return <AlertCircle className="w-5 h-5 text-orange-600" />
      case 'milestone':
        return <Star className="w-5 h-5 text-yellow-600" />
      case 'emergency_support':
        return <AlertCircle className="w-5 h-5 text-red-600" />
      default:
        return <Bell className="w-5 h-5" />
    }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - new Date(date).getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return 'Ahora'
    if (minutes < 60) return `hace ${minutes}m`
    if (hours < 24) return `hace ${hours}h`
    return `hace ${days}d`
  }

  return (
    <>
      {/* Notification Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <div className="fixed top-16 right-4 w-96 max-h-96 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden z-50">
          {/* Header */}
          <div className="bg-gradient-to-r from-brand-orange to-orange-500 p-4 flex items-center justify-between">
            <h2 className="text-white font-bold flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notificaciones
            </h2>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white/20 p-1 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Notifications List */}
          <div className="overflow-y-auto max-h-80">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>No hay notificaciones nuevas</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`border-b p-4 cursor-pointer transition-colors hover:bg-slate-50 ${
                    !notification.read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex gap-3">
                    {/* Icon */}
                    <div className="flex-shrink-0 mt-1">
                      {getTypeIcon(notification.type)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-semibold text-sm text-brand-night">
                            {notification.title}
                          </p>
                          <p className="text-sm text-slate-600 mt-1 line-clamp-2">
                            {notification.message}
                          </p>
                        </div>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0 mt-1" />
                        )}
                      </div>

                      <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                        <span>{formatTime(notification.timestamp)}</span>
                        {notification.platform && (
                          <span className="px-2 py-1 bg-slate-100 rounded text-slate-600">
                            {notification.platform}
                          </span>
                        )}
                      </div>

                      {/* Action Buttons */}
                      {notification.requiresApproval && (
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              approveAction(notification.id)
                            }}
                            className="flex-1 px-3 py-1.5 bg-green-500 text-white text-xs font-semibold rounded-lg hover:bg-green-600 transition-colors"
                          >
                            Aprobar
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              dismissNotification(notification.id)
                            }}
                            className="flex-1 px-3 py-1.5 bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-300 transition-colors"
                          >
                            Rechazar
                          </button>
                        </div>
                      )}

                      {notification.actionUrl && !notification.requiresApproval && (
                        <div className="mt-3">
                          <Link
                            href={notification.actionUrl}
                            onClick={(e) => {
                              setIsOpen(false)
                            }}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-brand-orange hover:text-orange-600 transition-colors"
                          >
                            Ver más →
                          </Link>
                        </div>
                      )}
                    </div>

                    {/* Dismiss Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        dismissNotification(notification.id)
                      }}
                      className="flex-shrink-0 text-slate-400 hover:text-slate-600 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="border-t p-3 bg-slate-50 text-center">
              <Link href="/dashboard/alertas" className="text-xs font-semibold text-brand-orange hover:text-orange-600">
                Ver todas las notificaciones →
              </Link>
            </div>
          )}
        </div>
      )}
    </>
  )
}

