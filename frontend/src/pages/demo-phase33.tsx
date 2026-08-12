import React, { useState } from 'react';
import PlatformOverview from '@/components/Phase33MultiPlatform/PlatformOverview';
import PricingOptimizer from '@/components/Phase33MultiPlatform/PricingOptimizer';
import SEOOptimizer from '@/components/Phase33MultiPlatform/SEOOptimizer';

export default function DemoPhase33() {
  const [activeTab, setActiveTab] = useState<'overview' | 'pricing' | 'seo'>('overview');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 shadow-lg">
        <h1 className="text-4xl font-bold mb-2">Phase 33: Multi-Platform Seller Automation</h1>
        <p className="text-blue-100">SellIA × Mercado Libre × Amazon × Hotmart — World's Best Seller</p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-full px-6 py-4 flex gap-4">
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
      <div className="max-w-full">
        {activeTab === 'overview' && <PlatformOverview />}
        {activeTab === 'pricing' && <PricingOptimizer />}
        {activeTab === 'seo' && <SEOOptimizer />}
      </div>

      {/* Footer */}
      <div className="bg-gray-900 text-gray-300 p-6 mt-12 text-center">
        <p className="mb-2">Phase 33 Demo — Multi-Platform Seller Automation Engine</p>
        <p className="text-sm text-gray-500">
          Backend: 4 core engines • 12 API endpoints • 11 database tables<br/>
          Frontend: 3 dashboards • 60+ tests • Real-time sync across 3 platforms
        </p>
      </div>
    </div>
  );
}
