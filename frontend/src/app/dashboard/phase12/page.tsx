'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SEOAnalyzer } from '@/components/Enterprise/SEOAnalyzer';
import { TrendingUp, BookOpen, Zap } from 'lucide-react';

export default function Phase12Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Phase 1-2: SEO Foundation
          </h1>
          <p className="text-lg text-slate-600">
            Structured data, Core Web Vitals, keyword optimization
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="analyzer" className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              SEO Analyzer
            </TabsTrigger>
            <TabsTrigger value="guide" className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              Implementation Guide
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="space-y-6">
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-slate-600">
                      Search Visibility
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-emerald-600">45%</div>
                    <p className="text-sm text-slate-600 mt-2">vs industry avg 32%</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-slate-600">
                      Organic Traffic
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-blue-600">+28%</div>
                    <p className="text-sm text-slate-600 mt-2">This month</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-slate-600">
                      Avg Ranking Position
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-purple-600">#4.2</div>
                    <p className="text-sm text-slate-600 mt-2">For target keywords</p>
                  </CardContent>
                </Card>
              </div>

              {/* Timeline */}
              <Card>
                <CardHeader>
                  <CardTitle>Phase Timeline</CardTitle>
                  <CardDescription>Implementation roadmap</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 bg-emerald-500 text-white rounded-full flex items-center justify-center font-bold">
                          ✓
                        </div>
                        <div className="w-0.5 h-12 bg-emerald-500 my-2"></div>
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">Week 1: Foundation</h3>
                        <p className="text-sm text-slate-600 mt-1">
                          Implement Product + Organization JSON-LD schemas, setup robots.txt
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">
                          ⚙
                        </div>
                        <div className="w-0.5 h-12 bg-slate-300 my-2"></div>
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">Week 2-3: Core Web Vitals</h3>
                        <p className="text-sm text-slate-600 mt-1">
                          Optimize LCP, FID, CLS. Image optimization, JS bundle reduction, preconnect
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 bg-slate-400 text-white rounded-full flex items-center justify-center font-bold">
                          →
                        </div>
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">Week 4: Keyword Optimization</h3>
                        <p className="text-sm text-slate-600 mt-1">
                          Target keywords in titles, H1s, bullet points. A/B test variations
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Analyzer Tab */}
          <TabsContent value="analyzer">
            <SEOAnalyzer />
          </TabsContent>

          {/* Guide Tab */}
          <TabsContent value="guide">
            <Card>
              <CardHeader>
                <CardTitle>Quick Start: JSON-LD Implementation</CardTitle>
                <CardDescription>Copy-paste schemas for your products</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="font-semibold text-slate-900 mb-2">Product Schema Example</h3>
                  <pre className="bg-slate-900 text-slate-100 p-4 rounded overflow-x-auto text-xs">
                    {`<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "Executive Anvil",
  "image": "https://example.com/anvil.jpg",
  "description": "Sleek and durable anvil",
  "brand": {
    "@type": "Brand",
    "name": "Acme"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/anvil",
    "priceCurrency": "USD",
    "price": "119.99",
    "priceFeelingType": "https://purl.org/goodrelations/v1#FixedPrice",
    "availability": "https://schema.org/InStock"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.4",
    "reviewCount": "88"
  }
}
</script>`}
                  </pre>
                </div>

                <div>
                  <h3 className="font-semibold text-slate-900 mb-2">Implementation Steps</h3>
                  <ol className="space-y-2 list-decimal list-inside text-slate-700">
                    <li>Add the JSON-LD block to your product page &lt;head&gt; or before &lt;/body&gt;</li>
                    <li>Replace values with actual product data (name, price, images, rating)</li>
                    <li>Test with Google Rich Results Test: https://search.google.com/test/rich-results</li>
                    <li>Monitor rich snippet appearance in Search Console</li>
                    <li>Repeat for all product variations</li>
                  </ol>
                </div>

                <div className="bg-blue-50 border border-blue-200 p-4 rounded">
                  <p className="text-sm text-blue-900">
                    <strong>💡 Pro Tip:</strong> Use dynamic schema generation on your backend. For each product, generate Product + Breadcrumb + Organization schemas at render time.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
