/**
 * FOOM Embeddable Widgets
 * Scarcity Counter, Countdown Timer, Activity Feed
 */

import React, { useEffect, useState } from 'react';

// ========== SCARCITY COUNTER ==========
interface ScarcityCounterProps {
  campaignId: string;
  total: number;
  label?: string;
  color?: string;
}

export const ScarcityCounter: React.FC<ScarcityCounterProps> = ({
  campaignId,
  total,
  label = 'en stock',
  color = '#ef4444',
}) => {
  const [available, setAvailable] = useState<number>(total);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAvailable = async () => {
      try {
        setLoading(true);
        const res = await fetch(`/api/fomo/events/${campaignId}/count?type=purchase`);
        const { count } = await res.json();
        setAvailable(Math.max(0, total - count));
      } catch (err) {
        console.error('Error fetching scarcity:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAvailable();
    const interval = setInterval(fetchAvailable, 5000);
    return () => clearInterval(interval);
  }, [campaignId, total]);

  const percentage = (available / total) * 100;
  const urgency = percentage < 20 ? 'high' : percentage < 50 ? 'medium' : 'low';

  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: `2px solid ${color}`,
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '14px', fontWeight: '600', color }}>
          {loading ? '...' : `${available}/${total}`} {label}
        </span>
        <div
          style={{
            height: '4px',
            backgroundColor: '#e5e7eb',
            borderRadius: '2px',
            flex: 1,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              backgroundColor:
                urgency === 'high' ? '#dc2626' : urgency === 'medium' ? '#f59e0b' : '#10b981',
              width: `${percentage}%`,
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>
    </div>
  );
};

// ========== COUNTDOWN TIMER ==========
interface CountdownTimerProps {
  campaignId: string;
  durationHours: number;
  label?: string;
  onExpired?: () => void;
}

export const CountdownTimer: React.FC<CountdownTimerProps> = ({
  campaignId,
  durationHours,
  label = 'Oferta válida por',
  onExpired,
}) => {
  const [remaining, setRemaining] = useState<string>('');

  useEffect(() => {
    const storageKey = `fomo_timer_${campaignId}`;
    const startTime = localStorage.getItem(storageKey) || new Date().toISOString();
    localStorage.setItem(storageKey, startTime);

    const updateTimer = () => {
      const now = new Date().getTime();
      const start = new Date(startTime).getTime();
      const totalMs = durationHours * 60 * 60 * 1000;
      const elapsed = now - start;
      const remainingMs = Math.max(0, totalMs - elapsed);

      if (remainingMs === 0) {
        setRemaining('EXPIRADO');
        onExpired?.();
        return;
      }

      const hours = Math.floor(remainingMs / (1000 * 60 * 60));
      const minutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((remainingMs % (1000 * 60)) / 1000);

      setRemaining(
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds
          .toString()
          .padStart(2, '0')}`
      );
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [campaignId, durationHours, onExpired]);

  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: '#fef2f2',
        borderRadius: '8px',
        border: '2px solid #dc2626',
        textAlign: 'center',
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <div style={{ fontSize: '12px', color: '#7f1d1d', fontWeight: '500' }}>
        {label}
      </div>
      <div
        style={{
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#dc2626',
          marginTop: '4px',
          fontFamily: 'monospace',
        }}
      >
        {remaining || '...'}
      </div>
    </div>
  );
};

// ========== ACTIVITY FEED ==========
interface Activity {
  id: string;
  event_type: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

interface ActivityFeedProps {
  campaignId: string;
  maxItems?: number;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  campaignId,
  maxItems = 5,
}) => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        setLoading(true);
        const res = await fetch(`/api/fomo/events/${campaignId}/recent?limit=${maxItems}`);
        const data = await res.json();
        setActivities(data);
      } catch (err) {
        console.error('Error fetching activities:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchActivities();
    const interval = setInterval(fetchActivities, 8000);
    return () => clearInterval(interval);
  }, [campaignId, maxItems]);

  const getLabel = (eventType: string): string => {
    const labels: Record<string, string> = {
      purchase: 'compró este producto',
      view: 'está viendo este producto',
      add_to_cart: 'agregó al carrito',
      abandoned: 'abandonó el carrito',
    };
    return labels[eventType] || eventType;
  };

  const getEmoji = (eventType: string): string => {
    const emojis: Record<string, string> = {
      purchase: '✓',
      view: '👁️',
      add_to_cart: '🛒',
      abandoned: '⏱️',
    };
    return emojis[eventType] || '•';
  };

  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        fontFamily: 'system-ui, sans-serif',
        maxWidth: '100%',
      }}
    >
      <div style={{ fontSize: '12px', fontWeight: '600', color: '#374151', marginBottom: '12px' }}>
        Actividad en tiempo real
      </div>
      {loading ? (
        <div style={{ fontSize: '12px', color: '#9ca3af' }}>Cargando...</div>
      ) : activities.length === 0 ? (
        <div style={{ fontSize: '12px', color: '#9ca3af' }}>Sin actividad aún</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {activities.map(activity => (
            <div
              key={activity.id}
              style={{
                fontSize: '12px',
                color: '#4b5563',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 0',
                borderBottom: '1px solid #e5e7eb',
                paddingBottom: '8px',
              }}
            >
              <span style={{ fontSize: '14px' }}>{getEmoji(activity.event_type)}</span>
              <span>
                <strong>{(activity.metadata?.customerName as string) || 'Usuario'}</strong>{' '}
                {getLabel(activity.event_type)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default {
  ScarcityCounter,
  CountdownTimer,
  ActivityFeed,
};
