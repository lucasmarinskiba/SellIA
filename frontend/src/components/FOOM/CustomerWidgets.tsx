/**
 * Customer-Facing FOOM Widgets
 * Embeddable widgets for customer websites
 */

import React, { useEffect, useState } from 'react';

// 1. Live Visitor Counter Widget
export const CustomerVisitorCounter: React.FC<{
  campaignId: string;
  updateFrequency?: number;
}> = ({ campaignId, updateFrequency = 5000 }) => {
  const [visitorCount, setVisitorCount] = useState(Math.floor(Math.random() * 500) + 100);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisitorCount((prev) => {
        const change = Math.floor(Math.random() * 5) - 2;
        return Math.max(1, prev + change);
      });
    }, updateFrequency);
    return () => clearInterval(interval);
  }, [updateFrequency]);

  return (
    <div
      style={{
        padding: '16px',
        backgroundColor: '#f0f9ff',
        borderRadius: '8px',
        border: '2px solid #0284c7',
        textAlign: 'center',
        fontFamily: 'sans-serif',
        maxWidth: '200px',
      }}
    >
      <div style={{ fontSize: '12px', fontWeight: '600', color: '#0c4a6e', marginBottom: '8px' }}>
        👥 Visitantes ahora
      </div>
      <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#0284c7' }}>
        {visitorCount}
      </div>
      <div style={{ fontSize: '10px', color: '#0c4a6e', marginTop: '4px' }}>
        personas viendo esto
      </div>
    </div>
  );
};

// 2. Recent Purchase Feed Widget
export const CustomerPurchaseFeed: React.FC<{ campaignId: string }> = ({ campaignId }) => {
  const [purchases, setPurchases] = useState([
    { id: 1, name: 'Juan M.', product: 'Product Pro', time: '2 min' },
    { id: 2, name: 'María L.', product: 'Product Plus', time: '5 min' },
    { id: 3, name: 'Carlos P.', product: 'Product Pro', time: '8 min' },
    { id: 4, name: 'Ana R.', product: 'Product Starter', time: '12 min' },
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      const names = ['Juan', 'María', 'Carlos', 'Ana', 'Pedro', 'Sofia', 'Diego', 'Laura'];
      const products = ['Product Pro', 'Product Plus', 'Product Starter'];
      const newPurchase = {
        id: Math.random(),
        name: names[Math.floor(Math.random() * names.length)] + ' ' + names[0][0],
        product: products[Math.floor(Math.random() * products.length)],
        time: 'Justo ahora',
      };
      setPurchases((prev) => [newPurchase, ...prev.slice(0, 3)]);
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      style={{
        width: '280px',
        maxHeight: '300px',
        backgroundColor: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        overflow: 'hidden',
        fontFamily: 'sans-serif',
      }}
    >
      <div style={{ padding: '12px 16px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ fontSize: '12px', fontWeight: '600', color: '#374151' }}>
          ✓ Compras verificadas
        </div>
      </div>
      <div style={{ maxHeight: '260px', overflowY: 'auto' }}>
        {purchases.map((purchase) => (
          <div
            key={purchase.id}
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid #f3f4f6',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '13px',
            }}
          >
            <div>
              <div style={{ fontWeight: '600', color: '#111' }}>{purchase.name}</div>
              <div style={{ fontSize: '11px', color: '#999' }}>{purchase.product}</div>
            </div>
            <div style={{ fontSize: '10px', color: '#999' }}>{purchase.time}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// 3. Countdown Timer Widget
export const CustomerCountdownTimer: React.FC<{
  campaignId: string;
  expiresAt: Date;
}> = ({ campaignId, expiresAt }) => {
  const [timeLeft, setTimeLeft] = useState<string>('');
  const [percentage, setPercentage] = useState(100);

  useEffect(() => {
    const update = () => {
      const now = new Date().getTime();
      const end = expiresAt.getTime();
      const remaining = end - now;

      if (remaining <= 0) {
        setTimeLeft('EXPIRADO');
        setPercentage(0);
        return;
      }

      const days = Math.floor(remaining / (1000 * 60 * 60 * 24));
      const hours = Math.floor((remaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));

      if (days > 0) {
        setTimeLeft(`${days}d ${hours}h`);
      } else if (hours > 0) {
        setTimeLeft(`${hours}h ${minutes}m`);
      } else {
        setTimeLeft(`${minutes}m`);
      }

      const total = expiresAt.getTime() - new Date('2026-08-25').getTime();
      setPercentage(Math.max(0, (remaining / total) * 100));
    };

    update();
    const interval = setInterval(update, 30000);
    return () => clearInterval(interval);
  }, [expiresAt]);

  return (
    <div
      style={{
        padding: '20px',
        backgroundColor: '#fef2f2',
        borderRadius: '8px',
        border: '2px solid #dc2626',
        textAlign: 'center',
        fontFamily: 'sans-serif',
        maxWidth: '280px',
      }}
    >
      <div style={{ fontSize: '12px', fontWeight: '600', color: '#991b1b', marginBottom: '8px' }}>
        ⏰ OFERTA POR TIEMPO LIMITADO
      </div>
      <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#dc2626', marginBottom: '12px' }}>
        {timeLeft}
      </div>
      <div
        style={{
          height: '8px',
          backgroundColor: '#fee2e2',
          borderRadius: '4px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            backgroundColor: '#dc2626',
            width: `${percentage}%`,
            transition: 'width 0.3s ease',
          }}
        />
      </div>
      <div style={{ fontSize: '11px', color: '#991b1b', marginTop: '8px', fontWeight: 'bold' }}>
        ¡Apúrate! Oferta expirando...
      </div>
    </div>
  );
};

// 4. Stock Scarcity Badge
export const CustomerStockBadge: React.FC<{
  campaignId: string;
  stock: number;
  threshold?: number;
}> = ({ campaignId, stock, threshold = 10 }) => {
  const isLow = stock < threshold;
  const isCritical = stock < 3;

  let message = `${stock} en stock`;
  let bgColor = '#f0fdf4';
  let borderColor = '#86efac';
  let textColor = '#166534';

  if (isCritical) {
    message = `¡SOLO ${stock}! APÚRATE`;
    bgColor = '#fef2f2';
    borderColor = '#fca5a5';
    textColor = '#991b1b';
  } else if (isLow) {
    message = `Solo ${stock} quedan`;
    bgColor = '#fef3c7';
    borderColor = '#fde047';
    textColor = '#92400e';
  }

  return (
    <div
      style={{
        padding: '8px 12px',
        backgroundColor: bgColor,
        border: `2px solid ${borderColor}`,
        borderRadius: '6px',
        fontSize: '12px',
        fontWeight: '600',
        color: textColor,
        fontFamily: 'sans-serif',
        display: 'inline-block',
        animation: isCritical ? 'pulse 1s infinite' : 'none',
      }}
    >
      📦 {message}
    </div>
  );
};

// 5. Trust Score / Reviews Badge
export const CustomerTrustBadge: React.FC<{
  rating: number;
  reviewCount: number;
}> = ({ rating, reviewCount }) => {
  const color = rating > 4.5 ? '#10b981' : rating > 3.5 ? '#f59e0b' : '#ef4444';

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
        fontFamily: 'sans-serif',
      }}
    >
      <span style={{ fontSize: '16px' }}>⭐</span>
      <div>
        <div style={{ fontSize: '12px', fontWeight: 'bold', color }}>
          {rating.toFixed(1)} ({reviewCount})
        </div>
        <div style={{ fontSize: '10px', color: '#666' }}>Altamente confiable</div>
      </div>
    </div>
  );
};

// 6. Urgency Banner
export const CustomerUrgencyBanner: React.FC<{
  campaignId: string;
  message: string;
  bgColor?: string;
}> = ({ campaignId, message, bgColor = '#FF6B6B' }) => {
  return (
    <div
      style={{
        padding: '16px',
        backgroundColor: bgColor,
        color: 'white',
        textAlign: 'center',
        fontWeight: 'bold',
        fontSize: '14px',
        borderRadius: '8px',
        animation: 'pulse 1s infinite',
        fontFamily: 'sans-serif',
      }}
    >
      {message}
    </div>
  );
};

// 7. Social Proof Widget - "Featured In"
export const CustomerFeaturedIn: React.FC<{
  logos: string[];
}> = ({ logos = ['TechCrunch', 'ProductHunt', 'Forbes'] }) => {
  return (
    <div style={{ textAlign: 'center', fontFamily: 'sans-serif' }}>
      <div style={{ fontSize: '12px', fontWeight: '600', color: '#666', marginBottom: '12px' }}>
        CONFIADO POR
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
        {logos.map((logo, i) => (
          <div
            key={i}
            style={{
              fontSize: '11px',
              fontWeight: '600',
              color: '#999',
              padding: '6px 12px',
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              backgroundColor: '#f9fafb',
            }}
          >
            {logo}
          </div>
        ))}
      </div>
    </div>
  );
};

// Aggregated Widget - Can be customized by user
export const CustomerFOOMWidget: React.FC<{
  campaignId: string;
  widgetType: string;
  config?: Record<string, any>;
}> = ({ campaignId, widgetType, config = {} }) => {
  switch (widgetType) {
    case 'visitor_counter':
      return <CustomerVisitorCounter campaignId={campaignId} {...config} />;
    case 'purchase_feed':
      return <CustomerPurchaseFeed campaignId={campaignId} />;
    case 'countdown':
      return (
        <CustomerCountdownTimer
          campaignId={campaignId}
          expiresAt={config.expiresAt || new Date(Date.now() + 24 * 60 * 60 * 1000)}
          {...config}
        />
      );
    case 'stock_badge':
      return <CustomerStockBadge campaignId={campaignId} stock={config.stock || 5} {...config} />;
    case 'trust_badge':
      return <CustomerTrustBadge rating={config.rating || 4.8} reviewCount={config.reviewCount || 284} />;
    case 'urgency_banner':
      return (
        <CustomerUrgencyBanner
          campaignId={campaignId}
          message={config.message || '⚡ OFERTA LIMITADA - SOLO DESDE HOY'}
          {...config}
        />
      );
    case 'featured_in':
      return <CustomerFeaturedIn logos={config.logos} />;
    default:
      return null;
  }
};

export default {
  CustomerVisitorCounter,
  CustomerPurchaseFeed,
  CustomerCountdownTimer,
  CustomerStockBadge,
  CustomerTrustBadge,
  CustomerUrgencyBanner,
  CustomerFeaturedIn,
  CustomerFOOMWidget,
};
