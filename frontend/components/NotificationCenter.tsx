import React, { useState, useEffect } from 'react';
import { Bell, Settings, X, CheckCircle, AlertCircle, Clock } from 'lucide-react';

const NotificationCenter: React.FC<{ businessId: string; userId: string }> = ({ businessId, userId }) => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [preferences, setPreferences] = useState<any>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    fetchNotifications();
    fetchPreferences();
  }, [businessId, userId]);

  const fetchNotifications = async () => {
    try {
      const res = await fetch(
        `/api/v1/users/${userId}/notifications/history?business_id=${businessId}&days=7`
      );
      const data = await res.json();
      setNotifications(Array.isArray(data) ? data : []);
      setUnreadCount(data.filter((n: any) => !n.read).length);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const fetchPreferences = async () => {
    try {
      const res = await fetch(
        `/api/v1/users/${userId}/notifications/preferences?business_id=${businessId}`
      );
      const data = await res.json();
      setPreferences(data);
    } catch (error) {
      console.error('Failed to fetch preferences:', error);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await fetch(`/api/v1/notifications/${notificationId}/read`, {
        method: 'POST'
      });
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const updatePreferences = async (updatedPrefs: any) => {
    try {
      await fetch(
        `/api/v1/users/${userId}/notifications/preferences?business_id=${businessId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedPrefs)
        }
      );
      fetchPreferences();
      setShowPreferences(false);
    } catch (error) {
      console.error('Failed to update preferences:', error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'text-red-600';
      case 'high':
        return 'text-orange-600';
      case 'medium':
        return 'text-yellow-600';
      default:
        return 'text-blue-600';
    }
  };

  const getPriorityBg = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-50 border-red-200';
      case 'high':
        return 'bg-orange-50 border-orange-200';
      case 'medium':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition"
      >
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Menu */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-2xl z-50 border border-gray-200">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 className="text-lg font-bold text-gray-900">Notificaciones</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowPreferences(!showPreferences)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={() => setShowDropdown(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>

          {/* Notifications List */}
          {!showPreferences && (
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Bell className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>Sin notificaciones</p>
                </div>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.notification_id}
                    className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition ${getPriorityBg(notification.priority)}`}
                    onClick={() => markAsRead(notification.notification_id)}
                  >
                    <div className="flex items-start gap-3">
                      {notification.priority === 'critical' || notification.priority === 'high' ? (
                        <AlertCircle className={`w-5 h-5 flex-shrink-0 mt-1 ${getPriorityColor(notification.priority)}`} />
                      ) : (
                        <CheckCircle className={`w-5 h-5 flex-shrink-0 mt-1 ${getPriorityColor(notification.priority)}`} />
                      )}
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900">{notification.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                        <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(notification.timestamp).toLocaleString('es-AR')}</span>
                          {notification.read && (
                            <span className="ml-auto bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                              Leído
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Preferences Panel */}
          {showPreferences && preferences && (
            <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
              <h4 className="font-semibold text-gray-900">Preferencias de notificación</h4>

              <div className="space-y-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={preferences.email_enabled}
                    onChange={(e) => updatePreferences({ email_enabled: e.target.checked })}
                    className="w-4 h-4 rounded"
                  />
                  <span className="text-sm text-gray-700">Email</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={preferences.sms_enabled}
                    onChange={(e) => updatePreferences({ sms_enabled: e.target.checked })}
                    className="w-4 h-4 rounded"
                  />
                  <span className="text-sm text-gray-700">SMS</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={preferences.whatsapp_enabled}
                    onChange={(e) => updatePreferences({ whatsapp_enabled: e.target.checked })}
                    className="w-4 h-4 rounded"
                  />
                  <span className="text-sm text-gray-700">WhatsApp</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={preferences.in_app_enabled}
                    onChange={(e) => updatePreferences({ in_app_enabled: e.target.checked })}
                    className="w-4 h-4 rounded"
                  />
                  <span className="text-sm text-gray-700">En la app</span>
                </label>
              </div>

              <div className="border-t border-gray-200 pt-4">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Horas silenciosas
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="time"
                    value={preferences.quiet_hours_start || '22:00'}
                    onChange={(e) => updatePreferences({ quiet_hours_start: e.target.value })}
                    className="px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                  <span className="text-gray-500">a</span>
                  <input
                    type="time"
                    value={preferences.quiet_hours_end || '08:00'}
                    onChange={(e) => updatePreferences({ quiet_hours_end: e.target.value })}
                    className="px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;
