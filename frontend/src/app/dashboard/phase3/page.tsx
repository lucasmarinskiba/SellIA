'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AuthorityBuilder } from '@/components/Enterprise/AuthorityBuilder';
import { BookOpen, Sparkles } from 'lucide-react';

export default function Phase3Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Phase 3: Authority Building
          </h1>
          <p className="text-lg text-slate-600">
            E-E-A-T signals: Expertise, Experience, Authoritativeness, Trustworthiness
          </p>
        </div>

        {/* Main Component */}
        <AuthorityBuilder />

        {/* Info Card */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              What is E-E-A-T?
            </CardTitle>
            <CardDescription>Google's framework for trustworthiness</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold text-slate-900 mb-2">Experience</h3>
                <p className="text-sm text-slate-600">
                  Years in business, track record, real customer results. Show longevity.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold text-slate-900 mb-2">Expertise</h3>
                <p className="text-sm text-slate-600">
                  Seller bio, certifications, specialties, media appearances.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold text-slate-900 mb-2">Authoritativeness</h3>
                <p className="text-sm text-slate-600">
                  LinkedIn profile, website, mentions in reputable publications.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold text-slate-900 mb-2">Trustworthiness</h3>
                <p className="text-sm text-slate-600">
                  Reviews, response rate, verified badges, transparent policies.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Timeline */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Implementation Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold">
                    ✓
                  </div>
                  <div className="w-0.5 h-12 bg-purple-500 my-2"></div>
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">Week 1: Testimonials</h3>
                  <p className="text-sm text-slate-600 mt-1">Collect 5-10 customer testimonials (text + video)</p>
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
                  <h3 className="font-semibold text-slate-900">Week 2: Seller Bio</h3>
                  <p className="text-sm text-slate-600 mt-1">Create profile: years in business, specialties, media links</p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 bg-slate-400 text-white rounded-full flex items-center justify-center font-bold">
                    →
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">Week 3-4: Reputation Management</h3>
                  <p className="text-sm text-slate-600 mt-1">Respond to all reviews. Register awards. Monitor trust score.</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
