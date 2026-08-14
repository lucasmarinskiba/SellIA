'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, AlertCircle, Zap } from 'lucide-react';

interface SEOMetric {
  name: string;
  value: number;
  target: number;
  status: 'good' | 'warning' | 'critical';
  description: string;
}

interface SEOData {
  pagespeed_score: number;
  cwv_lcp: number;
  cwv_fid: number;
  cwv_cls: number;
  mobile_friendly: boolean;
  schema_coverage: string[];
  keyword_optimization: number;
}

export const SEOAnalyzer: React.FC = () => {
  const [seoData, setSeoData] = useState<SEOData | null>(null);
  const [metrics, setMetrics] = useState<SEOMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [url, setUrl] = useState('');

  useEffect(() => {
    loadSEOData();
  }, []);

  const loadSEOData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/seo/analyze');
      if (response.ok) {
        const data = await response.json();
        setSeoData(data);
        calculateMetrics(data);
      } else {
        // Fallback to demo data
        const demoData: SEOData = {
          pagespeed_score: 76,
          cwv_lcp: 2.1,
          cwv_fid: 45,
          cwv_cls: 0.08,
          mobile_friendly: true,
          schema_coverage: ['Product', 'Organization', 'Breadcrumb'],
          keyword_optimization: 68,
        };
        setSeoData(demoData);
        calculateMetrics(demoData);
      }
    } catch (error) {
      console.error('SEO analysis error:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateMetrics = (data: SEOData) => {
    const newMetrics: SEOMetric[] = [
      {
        name: 'Page Speed',
        value: data.pagespeed_score,
        target: 90,
        status: data.pagespeed_score >= 90 ? 'good' : data.pagespeed_score >= 75 ? 'warning' : 'critical',
        description: 'Google PageSpeed Insights score',
      },
      {
        name: 'LCP (Largest Contentful Paint)',
        value: data.cwv_lcp,
        target: 2.5,
        status: data.cwv_lcp <= 2.5 ? 'good' : data.cwv_lcp <= 4 ? 'warning' : 'critical',
        description: `${data.cwv_lcp}s - Target: ≤2.5s`,
      },
      {
        name: 'FID (First Input Delay)',
        value: data.cwv_fid,
        target: 100,
        status: data.cwv_fid <= 100 ? 'good' : data.cwv_fid <= 300 ? 'warning' : 'critical',
        description: `${data.cwv_fid}ms - Target: ≤100ms`,
      },
      {
        name: 'CLS (Cumulative Layout Shift)',
        value: data.cwv_cls,
        target: 0.1,
        status: data.cwv_cls <= 0.1 ? 'good' : data.cwv_cls <= 0.25 ? 'warning' : 'critical',
        description: `${data.cwv_cls} - Target: ≤0.1`,
      },
      {
        name: 'Keyword Optimization',
        value: data.keyword_optimization,
        target: 85,
        status: data.keyword_optimization >= 85 ? 'good' : data.keyword_optimization >= 70 ? 'warning' : 'critical',
        description: 'Target keyword coverage analysis',
      },
    ];
    setMetrics(newMetrics);
  };

  const getStatusIcon = (status: string) => {
    if (status === 'good') return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    if (status === 'warning') return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    return <AlertCircle className="w-5 h-5 text-red-500" />;
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      good: 'default',
      warning: 'secondary',
      critical: 'destructive',
    };
    const labels = {
      good: 'Optimized',
      warning: 'Needs Work',
      critical: 'Critical',
    };
    return <Badge variant={variants[status]}>{labels[status]}</Badge>;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>SEO Analyzer</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const avgScore = metrics.length > 0 ? Math.round(metrics.reduce((sum, m) => sum + (m.value / m.target) * 100, 0) / metrics.length) : 0;

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            SEO Health Score
          </CardTitle>
          <CardDescription>Core Web Vitals + structured data coverage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-5xl font-bold text-emerald-600">{avgScore}</div>
              <p className="text-gray-600">Overall optimization score</p>
            </div>
            <div className="w-32 h-32 rounded-full border-8 border-emerald-600 flex items-center justify-center">
              <div className="text-3xl font-bold text-emerald-600">{avgScore}%</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {metrics.map((metric) => (
          <Card key={metric.name}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-lg">{metric.name}</h3>
                  <p className="text-sm text-gray-600">{metric.description}</p>
                </div>
                {getStatusIcon(metric.status)}
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        metric.status === 'good' ? 'bg-green-500' : metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min((metric.value / metric.target) * 100, 100)}%` }}
                    />
                  </div>
                </div>
                <span className="font-bold text-lg">{metric.value}</span>
              </div>
              <div className="mt-3">
                {getStatusBadge(metric.status)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Structured Data */}
      {seoData && (
        <Card>
          <CardHeader>
            <CardTitle>Structured Data (Schema.org)</CardTitle>
            <CardDescription>JSON-LD implementations detected</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {seoData.schema_coverage.length > 0 ? (
                seoData.schema_coverage.map((schema) => (
                  <Badge key={schema} variant="outline" className="flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {schema}
                  </Badge>
                ))
              ) : (
                <p className="text-gray-600">No structured data found. Implement JSON-LD schemas for better SERP visibility.</p>
              )}
            </div>
            {seoData.mobile_friendly && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
                <p className="text-sm text-green-800">✓ Mobile-friendly design detected</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Wins</CardTitle>
          <CardDescription>Top priority improvements</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {avgScore < 90 && (
              <li className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Improve Core Web Vitals</p>
                  <p className="text-sm text-gray-600">Optimize images, reduce JS, enable preconnect to external domains</p>
                </div>
              </li>
            )}
            {!seoData?.schema_coverage.includes('Product') && (
              <li className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Add Product Schema</p>
                  <p className="text-sm text-gray-600">Implement Product schema for rich snippets in search results</p>
                </div>
              </li>
            )}
            {metrics.find((m) => m.name === 'Keyword Optimization')?.value < 80 && (
              <li className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Target Keywords in Copy</p>
                  <p className="text-sm text-gray-600">Include primary keywords in H1, first paragraph, and meta description</p>
                </div>
              </li>
            )}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

