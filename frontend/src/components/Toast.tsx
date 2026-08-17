'use client'

import { X, CheckCircle, AlertCircle, Info, XCircle } from 'lucide-react'
import { Notification } from '@/app/providers'

interface ToastProps {
  notification: Notification
  onDismiss: (id: string) => void
}

export function Toast({ notification, onDismiss }: ToastProps) {
  const icons = {
    success: <CheckCircle size={20} className="text-green-600" />,
    error: <XCircle size={20} className="text-red-600" />,
    warning: <AlertCircle size={20} className="text-yellow-600" />,
    info: <Info size={20} className="text-blue-600" />,
  }

  const bgColors = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200',
    info: 'bg-blue-50 border-blue-200',
  }

  const textColors = {
    success: 'text-green-900',
    error: 'text-red-900',
    warning: 'text-yellow-900',
    info: 'text-blue-900',
  }

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${bgColors[notification.type]} animate-in slide-in-from-right`}
      role="alert"
    >
      {icons[notification.type]}
      <p className={`flex-1 text-sm font-medium ${textColors[notification.type]}`}>{notification.message}</p>
      <button onClick={() => onDismiss(notification.id)} className="p-1 hover:bg-black/5 rounded">
        <X size={16} />
      </button>
    </div>
  )
}
