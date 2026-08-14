'use client';

import React, { useState } from 'react';
import PlatformOverview from '@/components/Phase33MultiPlatform/PlatformOverview';
import PricingOptimizer from '@/components/Phase33MultiPlatform/PricingOptimizer';
import SEOOptimizer from '@/components/Phase33MultiPlatform/SEOOptimizer';

export default function Phase33Dashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'pricing' | 'seo'>('overview');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 shadow-lg mb-6">
        <h1 className="text-4xl font-bold mb-2">🚀 Phase 33: Multi-Platform Seller Automation</h1>
        <p className="text-blue-100">Real-time sync across Mercado Libre, Amazon, and Hotmart with dynamic pricing & SEO optimization</p>
      </div>

      {/* Tab Navigation */}
      <div className="sticky top-0 z-10 bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4 flex gap-4">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-6 py-2 font-semibold rounded-lg transition ${
              activeTab === 'overview'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            📊 Platform Overview
          </button>
          <button
            onClick={() => setActiveTab('pricing')}
            className={`px-6 py-2 font-semibold rounded-lg transition ${
              activeTab === 'pricing'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            💰 Pricing Optimizer
          </button>
          <button
            onClick={() => setActiveTab('seo')}
            className={`px-6 py-2 font-semibold rounded-lg transition ${
              activeTab === 'seo'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            🔍 SEO Optimizer
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {activeTab === 'overview' && <PlatformOverview />}
        {activeTab === 'pricing' && <PricingOptimizer />}
        {activeTab === 'seo' && <SEOOptimizer />}
      </div>
    </div>
  );
}

