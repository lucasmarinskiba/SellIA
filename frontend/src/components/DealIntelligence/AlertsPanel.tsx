/**
 * Alerts & Recommendations Panel
 * Shows recommended actions and risk alerts
 */

"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

interface Recommendation {
  action: string;
  priority: string;
  description: string;
}

interface Props {
  recommendations: Recommendation[];
  riskIndicators: Record<string, any>;
}

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-blue-100 text-blue-800",
};

const ACTION_ICONS: Record<string, string> = {
  "Call economic buyer": "📞",
  "Increase touchpoints": "💬",
  "Stakeholder mapping": "👥",
  "Competitive response": "⚔️",
  "Schedule demo": "🎬",
  "Send proposal": "📄",
};

export default function AlertsPanel({ recommendations, riskIndicators }: Props) {
  return (
    <div className="space-y-6">
      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Recommended Actions</h2>
          <div className="space-y-3">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border-l-4 ${
                  rec.priority === "high"
                    ? "bg-red-50 border-red-400"
                    : rec.priority === "medium"
                      ? "bg-yellow-50 border-yellow-400"
                      : "bg-blue-50 border-blue-400"
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">
                      {ACTION_ICONS[rec.action] || "→"}
                    </span>
                    <h3 className="font-bold">{rec.action}</h3>
                  </div>
                  <Badge className={PRIORITY_COLORS[rec.priority]}>
                    {rec.priority.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-sm text-gray-700">{rec.description}</p>
                <button className="mt-3 px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50 font-medium">
                  Take Action
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Risk Alerts */}
      {riskIndicators && (
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Risk Assessment</h2>
          <div className="space-y-3">
            {/* Inactivity Alert */}
            {riskIndicators.days_since_activity > 14 && (
              <Alert className="bg-red-50 border-red-200">
                <AlertDescription className="text-red-800">
                  <strong>⚠ High Inactivity:</strong> No engagement for {riskIndicators.days_since_activity} days.
                  Schedule immediate touchpoint.
                </AlertDescription>
              </Alert>
            )}

            {/* Stakeholder Churn Alert */}
            {riskIndicators.stakeholder_churn > 0 && (
              <Alert className="bg-yellow-50 border-yellow-200">
                <AlertDescription className="text-yellow-800">
                  <strong>⚠ Stakeholder Churn:</strong> {riskIndicators.stakeholder_churn} stakeholder(s) showing low
                  engagement. Re-engage to avoid deal loss.
                </AlertDescription>
              </Alert>
            )}

            {/* Economic Buyer Alert */}
            {!riskIndicators.economic_buyer_engaged && (
              <Alert className="bg-red-50 border-red-200">
                <AlertDescription className="text-red-800">
                  <strong>✗ Economic Buyer Not Engaged:</strong> Critical decision-maker has low activity. Priority:
                  identify and engage.
                </AlertDescription>
              </Alert>
            )}

            {/* Positive Indicators */}
            {riskIndicators.days_since_activity <= 7 &&
              riskIndicators.economic_buyer_engaged &&
              riskIndicators.stakeholder_churn === 0 && (
                <Alert className="bg-green-50 border-green-200">
                  <AlertDescription className="text-green-800">
                    <strong>✓ Deal on Track:</strong> Strong engagement, economic buyer active, no churn. Momentum is
                    positive.
                  </AlertDescription>
                </Alert>
              )}
          </div>
        </Card>
      )}

      {/* Next Steps */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h2 className="text-lg font-bold mb-3">Next Steps</h2>
        <ol className="space-y-2 list-decimal list-inside text-sm text-gray-700">
          <li>Review recommended actions above</li>
          <li>Schedule highest-priority action (call, demo, or proposal)</li>
          <li>Update deal status and stakeholder engagement</li>
          <li>Check health score daily (target: 70+)</li>
          <li>Re-run analysis weekly to track momentum</li>
        </ol>
      </Card>
    </div>
  );
}

