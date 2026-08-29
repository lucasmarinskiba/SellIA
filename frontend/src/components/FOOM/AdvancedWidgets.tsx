/**
 * Advanced FOOM Widgets
 * Rotating banners, purchase streak, milestones, personalized offers
 */

import React, { useEffect, useState } from 'react';

// 1. Rotating FOMO Banner
export const RotatingFOMOBanner: React.FC<{
  messages: Array<{ text: string; color: string; emoji: string }>;
}> = ({ messages }) => {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % messages.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [messages.length]);

  const msg = messages[index];

  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: msg.color,
        color: 'white',
        borderRadius: '8px',
        textAlign: 'center',
        fontWeight: 'bold',
        fontSize: '14px',
        animation: 'fadeIn 0.5s ease',
      }}
    >
      {msg.emoji} {msg.text}
    </div>
  );
};

// 2. Purchase Streak Counter
export const PurchaseStreak: React.FC<{ campaignId: string }> = ({ campaignId }) => {
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    const fetchStreak = async () => {
      const res = await fetch(`/api/fomo/events/${campaignId}/count?type=purchase&hours=1`);
      const { count } = await res.json();
      setStreak(count);
    };

    fetchStreak();
    const interval = setInterval(fetchStreak, 10000);
    return () => clearInterval(interval);
  }, [campaignId]);

  return (
    <div
      style={{
        padding: '16px',
        backgroundColor: '#fff7ed',
        borderRadius: '8px',
        textAlign: 'center',
        border: '2px solid #f97316',
      }}
    >
      <div style={{ fontSize: '12px', fontWeight: '600', color: '#b45309', marginBottom: '8px' }}>
        🔥 Buying Streak
      </div>
      <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#ea580c' }}>
        {streak}
      </div>
      <div style={{ fontSize: '12px', color: '#92400e', marginTop: '4px' }}>
        compras en la última hora
      </div>
    </div>
  );
};

// 3. Progress to Milestone
export const MilestoneProgress: React.FC<{
  current: number;
  milestone: number;
  label: string;
  unit?: string;
}> = ({ current, milestone, label, unit = '' }) => {
  const pct = Math.min((current / milestone) * 100, 100);
  const remaining = milestone - current;

  return (
    <div style={{ padding: '16px', backgroundColor: '#fef2f2', borderRadius: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '12px', fontWeight: '600', color: '#7f1d1d' }}>
          {label}
        </span>
        <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#dc2626' }}>
          {current}/{milestone} {unit}
        </span>
      </div>

      <div style={{ height: '8px', backgroundColor: '#fee2e2', borderRadius: '4px', overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            backgroundColor: '#dc2626',
            width: `${pct}%`,
            transition: 'width 0.3s ease',
          }}
        />
      </div>

      {pct >= 90 && (
        <div style={{ fontSize: '11px', color: '#dc2626', marginTop: '8px', fontWeight: 'bold' }}>
          🎉 ¡Casi lo logramos! {remaining} {unit} falta
        </div>
      )}
    </div>
  );
};

// 4. Personalized Offer Widget
export const PersonalizedOfferWidget: React.FC<{ userId: string }> = ({ userId }) => {
  const [offer, setOffer] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOffer = async () => {
      try {
        setLoading(true);
        const res = await fetch(`/api/fomo/personalized-offer/${userId}`);
        const data = await res.json();
        setOffer(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchOffer();
  }, [userId]);

  if (loading || !offer) return null;

  return (
    <div
      style={{
        padding: '20px',
        background: `linear-gradient(135deg, ${offer.color1}, ${offer.color2})`,
        color: 'white',
        borderRadius: '12px',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>
        {offer.headline}
      </div>
      <div style={{ fontSize: '36px', fontWeight: 'bold', marginBottom: '8px' }}>
        {offer.discount}% OFF
      </div>
      <div style={{ fontSize: '12px', marginBottom: '16px', opacity: 0.9 }}>
        {offer.subheadline}
      </div>
      <button
        onClick={() => {
          localStorage.setItem('promo_code', offer.code);
          window.location.href = '/checkout';
        }}
        style={{
          width: '100%',
          padding: '12px',
          backgroundColor: 'white',
          color: offer.color1,
          fontWeight: 'bold',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '14px',
        }}
      >
        Usar Código: {offer.code}
      </button>
    </div>
  );
};

// 5. Live Visitor Count
export const LiveVisitorCount: React.FC<{ initialCount?: number }> = ({
  initialCount = 280,
}) => {
  const [count, setCount] = useState(initialCount);

  useEffect(() => {
    // Simulate visitor count changes
    const interval = setInterval(() => {
      setCount((prev) => prev + Math.random() > 0.5 ? 1 : -1);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: '#f0f9ff',
        borderRadius: '8px',
        border: '2px solid #0284c7',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '11px', fontWeight: '600', color: '#0c4a6e', marginBottom: '4px' }}>
        👥 Visitantes ahora
      </div>
      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0284c7' }}>
        {Math.max(1, count)}
      </div>
    </div>
  );
};

// 6. Exclusive Access Timer
export const ExclusiveAccessTimer: React.FC<{ expiresAt: Date }> = ({ expiresAt }) => {
  const [timeLeft, setTimeLeft] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date().getTime();
      const end = expiresAt.getTime();
      const remaining = end - now;

      if (remaining <= 0) {
        setTimeLeft('EXPIRADO');
        return;
      }

      const hours = Math.floor(remaining / (1000 * 60 * 60));
      const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));

      setTimeLeft(`${hours}h ${minutes}m`);
    };

    update();
    const interval = setInterval(update, 60000);
    return () => clearInterval(interval);
  }, [expiresAt]);

  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: '#fce7f3',
        borderRadius: '8px',
        border: '2px solid #ec4899',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '11px', fontWeight: '600', color: '#831843', marginBottom: '4px' }}>
        ⏱️ Acceso exclusivo válido por
      </div>
      <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#ec4899' }}>
        {timeLeft}
      </div>
    </div>
  );
};

// 7. Trust Score Badge
export const TrustScoreBadge: React.FC<{ score: number }> = ({ score }) => {
  const color = score > 4.5 ? '#10b981' : score > 3.5 ? '#f59e0b' : '#ef4444';
  const label = score > 4.5 ? 'Altamente Confiable' : score > 3.5 ? 'Confiable' : 'Verificado';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 12px',
        backgroundColor: `${color}20`,
        borderRadius: '6px',
        border: `1px solid ${color}`,
      }}
    >
      <span style={{ fontSize: '18px' }}>⭐</span>
      <div>
        <div style={{ fontSize: '12px', fontWeight: 'bold', color }}>
          {score.toFixed(1)}
        </div>
        <div style={{ fontSize: '10px', color }}>
          {label}
        </div>
      </div>
    </div>
  );
};

export default {
  RotatingFOMOBanner,
  PurchaseStreak,
  MilestoneProgress,
  PersonalizedOfferWidget,
  LiveVisitorCount,
  ExclusiveAccessTimer,
  TrustScoreBadge,
};
