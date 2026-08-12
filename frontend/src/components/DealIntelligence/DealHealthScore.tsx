/**
 * Deal Health Score Component
 * Shows health metrics breakdown
 */

"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface HealthData {
  health_score: number;
  health_status: string;
  engagement_health: number;
  momentum_health: number;
  buyer_health: number;
  competition_health: number;
  risk_indicators: Record<string, any>;
  recommended_actions: any[];
}

interface Props {
  health: HealthData;
}

const getHealthColor = (score: number): string => {
  if (score >= 70) return "text-green-600";
  if (score >= 50) return "text-yellow-600";
  return "text-red-600";
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case "healthy":
      return "bg-green-50 border-green-200";
    case "at_risk":
      return "bg-yellow-50 border-yellow-200";
    case "critical":
      return "bg-red-50 border-red-200";
    default:
      return "bg-gray-50 border-gray-200";
  }
};

export default function DealHealthScore({ health }: Props) {
  return (
    <Card className={`p-6 border ${getStatusColor(health.health_status)}`}>
      <h2 className="text-xl font-bold mb-6">Deal Health Analysis</h2>

      {/* Overall Score */}
      <div className="mb-8 pb-6 border-b">
        <div className="flex justify-between items-end mb-2">
          <span className="text-gray-700 font-medium">Overall Health Score</span>
          <span className={`text-3xl font-bold ${getHealthColor(health.health_score)}`}>
            {health.health_score}/100
          </span>
        </div>
        <Progress value={health.health_score} className="h-3" />
        <p className="text-sm text-gray-600 mt-2 capitalize">
          Status: <span className="font-semibold">{health.health_status}</span>
        </p>
      </div>

      {/* Component Scores */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Engagement Health */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium text-gray-700">Engagement Health</label>
            <span className={`text-lg font-bold ${getHealthColor(health.engagement_health)}`}>
              {health.engagement_health}%
            </span>
          </div>
          <Progress value={health.engagement_health} className="h-2" />
          <p className="text-xs text-gray-500 mt-1">Stakeholder activity & involvement</p>
        </div>

        {/* Momentum Health */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium text-gray-700">Momentum Health</label>
            <span className={`text-lg font-bold ${getHealthColor(health.momentum_health)}`}>
              {health.momentum_health}%
            </span>
          </div>
          <Progress value={health.momentum_health} className="h-2" />
          <p className="text-xs text-gray-500 mt-1">Deal progression velocity</p>
        </div>

        {/* Buyer Health */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium text-gray-700">Buyer Health</label>
            <span className={`text-lg font-bold ${getHealthColor(health.buyer_health)}`}>
              {health.buyer_health}%
            </span>
          </div>
          <Progress value={health.buyer_health} className="h-2" />
          <p className="text-xs text-gray-500 mt-1">Economic buyer engagement</p>
        </div>

        {/* Competition Health */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium text-gray-700">Competition Health</label>
            <span className={`text-lg font-bold ${getHealthColor(health.competition_health)}`}>
              {health.competition_health}%
            </span>
          </div>
          <Progress value={health.competition_health} className="h-2" />
          <p className="text-xs text-gray-500 mt-1">Competitive threat level</p>
        </div>
      </div>

      {/* Risk Indicators */}
      {Object.keys(health.risk_indicators).length > 0 && (
        <div className="pt-6 border-t">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Risk Indicators</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Days Since Activity:</span>
              <span className={health.risk_indicators.days_since_activity > 14 ? "text-red-600 font-medium" : "text-gray-600"}>
                {health.risk_indicators.days_since_activity} days
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Stakeholder Churn:</span>
              <span className={health.risk_indicators.stakeholder_churn > 0 ? "text-yellow-600 font-medium" : "text-green-600"}>
                {health.risk_indicators.stakeholder_churn} at risk
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Economic Buyer Engaged:</span>
              <span className={health.risk_indicators.economic_buyer_engaged ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
                {health.risk_indicators.economic_buyer_engaged ? "✓ Yes" : "✗ No"}
              </span>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
