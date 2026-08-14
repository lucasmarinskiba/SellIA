'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Award, Star, MessageSquare, Trophy, TrendingUp } from 'lucide-react';

interface TrustScoreData {
  trust_score: number;
  tier: string;
  components: {
    review_rating: number;
    review_count: number;
    response_rate: number;
    verification: number;
    longevity_years: number;
  };
  next_tier: string | null;
  points_to_next: number;
}

export const AuthorityBuilder: React.FC = () => {
  const [trustData, setTrustData] = useState<TrustScoreData | null>(null);
  const [testimonials, setTestimonials] = useState<any[]>([]);
  const [awards, setAwards] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAuthorityData();
  }, []);

  const loadAuthorityData = async () => {
    try {
      setLoading(true);
      // Fetch trust score
      const trustRes = await fetch('/api/v1/authority/trust-score/demo-seller');
      if (trustRes.ok) {
        const trustData = await trustRes.json();
        setTrustData(trustData);
      }

      // Fallback demo data
      if (!trustData) {
        setTrustData({
          trust_score: 82.5,
          tier: 'gold',
          components: {
            review_rating: 4.7,
            review_count: 234,
            response_rate: 92.5,
            verification: 85,
            longevity_years: 8,
          },
          next_tier: 'platinum',
          points_to_next: 7.5,
        });
      }
    } catch (error) {
      console.error('Authority data load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTierColor = (tier: string) => {
    const colors: Record<string, string> = {
      platinum: 'text-yellow-500',
      gold: 'text-amber-500',
      silver: 'text-gray-400',
      bronze: 'text-amber-700',
    };
    return colors[tier] || 'text-gray-500';
  };

  const getTierBg = (tier: string) => {
    const bgs: Record<string, string> = {
      platinum: 'bg-yellow-50',
      gold: 'bg-amber-50',
      silver: 'bg-gray-50',
      bronze: 'bg-amber-50 opacity-50',
    };
    return bgs[tier] || 'bg-gray-50';
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Authority Builder</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Trust Score Card */}
      {trustData && (
        <Card className={`${getTierBg(trustData.tier)}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className={`w-5 h-5 ${getTierColor(trustData.tier)}`} />
              Trust & Authority Score
            </CardTitle>
            <CardDescription>E-E-A-T signals for buyer confidence</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="flex items-center justify-center">
                <div className="relative w-48 h-48">
                  <svg className="w-full h-full" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="90" fill="none" stroke="currentColor" strokeWidth="8" className="text-gray-200" />
                    <circle
                      cx="100"
                      cy="100"
                      r="90"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="8"
                      strokeDasharray={`${(trustData.trust_score / 100) * 565} 565`}
                      className={getTierColor(trustData.tier)}
                      style={{ transform: 'rotate(-90deg)', transformOrigin: '100px 100px' }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <div className={`text-4xl font-bold ${getTierColor(trustData.tier)}`}>
                      {trustData.trust_score}
                    </div>
                    <div className={`text-sm font-semibold uppercase ${getTierColor(trustData.tier)}`}>
                      {trustData.tier}
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 mb-2">Review Rating</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 h-2 rounded">
                      <div className="bg-yellow-500 h-full rounded" style={{ width: `${(trustData.components.review_rating / 5) * 100}%` }} />
                    </div>
                    <span className="font-bold text-lg">{trustData.components.review_rating}/5</span>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600 mb-2">Response Rate</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 h-2 rounded">
                      <div className="bg-blue-500 h-full rounded" style={{ width: `${trustData.components.response_rate}%` }} />
                    </div>
                    <span className="font-bold text-lg">{trustData.components.response_rate.toFixed(0)}%</span>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600 mb-2">Verification Score</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 h-2 rounded">
                      <div className="bg-green-500 h-full rounded" style={{ width: `${trustData.components.verification}%` }} />
                    </div>
                    <span className="font-bold text-lg">{trustData.components.verification.toFixed(0)}%</span>
                  </div>
                </div>

                {trustData.next_tier && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                    <p className="text-sm text-blue-900">
                      <strong>Next Tier:</strong> {trustData.next_tier} ({trustData.points_to_next.toFixed(1)} points)
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs defaultValue="testimonials" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="testimonials" className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Testimonials
          </TabsTrigger>
          <TabsTrigger value="awards" className="flex items-center gap-2">
            <Award className="w-4 h-4" />
            Awards
          </TabsTrigger>
          <TabsTrigger value="recommendations" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Roadmap
          </TabsTrigger>
        </TabsList>

        {/* Testimonials Tab */}
        <TabsContent value="testimonials">
          <Card>
            <CardHeader>
              <CardTitle>Customer Testimonials</CardTitle>
              <CardDescription>Social proof for higher conversion</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                {
                  name: 'María García',
                  title: 'Increased sales by 45%',
                  text: 'This seller provided exceptional support and fast shipping. Highly recommended!',
                  rating: 5,
                },
                {
                  name: 'Carlos López',
                  title: 'Professional & reliable',
                  text: 'Been buying for 2 years, never had an issue. Top-tier service.',
                  rating: 5,
                },
                {
                  name: 'Ana Martínez',
                  title: 'Best in category',
                  text: 'Quality products and customer service that actually listens.',
                  rating: 4,
                },
              ].map((testimonial, i) => (
                <div key={i} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p className="font-semibold text-slate-900">{testimonial.name}</p>
                      <p className="text-sm text-slate-600">{testimonial.title}</p>
                    </div>
                    <div className="flex gap-1">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                      ))}
                    </div>
                  </div>
                  <p className="text-slate-700">{testimonial.text}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Awards Tab */}
        <TabsContent value="awards">
          <Card>
            <CardHeader>
              <CardTitle>Certifications & Awards</CardTitle>
              <CardDescription>Trust badges from platforms & organizations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { name: 'Top Seller', issuer: 'Mercado Libre', year: 2024 },
                { name: 'Excellence Award', issuer: 'Amazon', year: 2024 },
                { name: 'Certified Professional', issuer: 'Hotmart', year: 2023 },
              ].map((award, i) => (
                <div key={i} className="flex items-center gap-3 p-3 border rounded-lg">
                  <Trophy className="w-5 h-5 text-amber-500" />
                  <div className="flex-1">
                    <p className="font-semibold text-slate-900">{award.name}</p>
                    <p className="text-sm text-slate-600">{award.issuer} • {award.year}</p>
                  </div>
                  <Badge variant="outline">Active</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations">
          <Card>
            <CardHeader>
              <CardTitle>Authority Building Roadmap</CardTitle>
              <CardDescription>E-E-A-T improvement strategy</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                {
                  priority: 1,
                  action: 'Respond to all reviews within 24h',
                  impact: '+15% trust score',
                  effort: '15 min/day',
                },
                {
                  priority: 2,
                  action: 'Collect 10 video testimonials',
                  impact: '+20% CTR',
                  effort: '2-3 days',
                },
                {
                  priority: 3,
                  action: 'Add seller bio + LinkedIn profile',
                  impact: '+10% authority',
                  effort: '30 min',
                },
              ].map((item) => (
                <div key={item.priority} className="flex gap-4 p-4 border rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold flex-shrink-0">
                    {item.priority}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-slate-900">{item.action}</p>
                    <p className="text-sm text-slate-600 mt-1">{item.impact} • Effort: {item.effort}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
