/**
 * Deal Detail Page with Intelligence
 * Shows stakeholders, probability prediction, health score, and recommendations
 */

"use client";

import React, { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import StakeholderMap from "./StakeholderMap";
import DealHealthScore from "./DealHealthScore";
import AlertsPanel from "./AlertsPanel";

interface DealIntelligence {
  deal_id: string;
  stakeholders: any[];
  probability: {
    close_probability: number;
    confidence_level: number;
    probability_low: number;
    probability_high: number;
    model_version: string;
  };
  health: {
    health_score: number;
    health_status: string;
    engagement_health: number;
    momentum_health: number;
    buyer_health: number;
    competition_health: number;
    risk_indicators: Record<string, any>;
    recommended_actions: Array<{
      action: string;
      priority: string;
      description: string;
    }>;
  };
}

interface Props {
  dealId: string;
}

export default function DealDetailWithIntelligence({ dealId }: Props) {
  const [intelligence, setIntelligence] = useState<DealIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchIntelligence();
  }, [dealId]);

  const fetchIntelligence = async () => {
    try {
      const res = await fetch(`/api/v1/intelligence/deal/${dealId}`);
      if (res.ok) {
        const data = await res.json();
        setIntelligence(data);
        setError("");
      } else {
        setError("Failed to load deal intelligence");
      }
    } catch (error) {
      setError("Network error loading intelligence");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchIntelligence();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4 animate-pulse" />
        <div className="h-64 bg-gray-200 rounded animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="bg-red-50 border-red-200">
        <AlertDescription className="text-red-800">✗ {error}</AlertDescription>
      </Alert>
    );
  }

  if (!intelligence) {
    return <div className="text-gray-600">No deal found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Deal Intelligence</h1>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {refreshing ? "Refreshing..." : "↻ Refresh"}
        </button>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Close Probability Card */}
        <Card className="p-6">
          <p className="text-gray-600 text-sm uppercase tracking-wide mb-2">Close Probability</p>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-bold text-blue-600">
              {Math.round(intelligence.probability.close_probability)}%
            </span>
            <span className="text-sm text-gray-500">±{Math.round(intelligence.probability.probability_high - intelligence.probability.close_probability)}%</span>
          </div>
          <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600"
              style={{
                width: `${Math.min(intelligence.probability.close_probability, 100)}%`,
              }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Confidence: {Math.round(intelligence.probability.confidence_level)}%
          </p>
        </Card>

        {/* Deal Health Card */}
        <Card className="p-6">
          <p className="text-gray-600 text-sm uppercase tracking-wide mb-2">Deal Health</p>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-bold">{intelligence.health.health_score}</span>
            <span className="text-sm">/100</span>
          </div>
          <div className="mt-3">
            <Badge
              className={
                intelligence.health.health_status === "healthy"
                  ? "bg-green-100 text-green-800"
                  : intelligence.health.health_status === "at_risk"
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-red-100 text-red-800"
              }
            >
              {intelligence.health.health_status.toUpperCase()}
            </Badge>
          </div>
          <div className="mt-3 space-y-1 text-xs text-gray-600">
            <div>Engagement: {intelligence.health.engagement_health}/100</div>
            <div>Momentum: {intelligence.health.momentum_health}/100</div>
            <div>Buyer: {intelligence.health.buyer_health}/100</div>
          </div>
        </Card>

        {/* Stakeholders Card */}
        <Card className="p-6">
          <p className="text-gray-600 text-sm uppercase tracking-wide mb-2">Buying Committee</p>
          <div className="text-4xl font-bold mb-3">{intelligence.stakeholders.length}</div>
          <div className="space-y-2 text-sm">
            {intelligence.stakeholders.slice(0, 3).map((s) => (
              <div key={s.person_id} className="flex justify-between">
                <span className="font-medium">{s.name}</span>
                <span className="text-gray-500">{Math.round(s.engagement_score)}%</span>
              </div>
            ))}
            {intelligence.stakeholders.length > 3 && (
              <p className="text-gray-500 text-xs">+{intelligence.stakeholders.length - 3} more</p>
            )}
          </div>
        </Card>
      </div>

      {/* Stakeholder Map */}
      <StakeholderMap stakeholders={intelligence.stakeholders} />

      {/* Health Details */}
      <DealHealthScore health={intelligence.health} />

      {/* Recommendations & Alerts */}
      <AlertsPanel
        recommendations={intelligence.health.recommended_actions}
        riskIndicators={intelligence.health.risk_indicators}
      />
    </div>
  );
}

