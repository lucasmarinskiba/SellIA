/**
 * Stakeholder Map Component
 * Visual representation of buying committee
 */

"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Stakeholder {
  person_id: string;
  email: string;
  name: string;
  title: string;
  buyer_role: string;
  influence_level: number;
  engagement_score: number;
  email_open_count: number;
  meeting_count: number;
  last_activity?: string;
}

interface Props {
  stakeholders: Stakeholder[];
}

const ROLE_COLORS: Record<string, string> = {
  economic_buyer: "bg-red-100 text-red-800 border-red-300",
  user_buyer: "bg-blue-100 text-blue-800 border-blue-300",
  coach: "bg-green-100 text-green-800 border-green-300",
  blocker: "bg-yellow-100 text-yellow-800 border-yellow-300",
  influencer: "bg-purple-100 text-purple-800 border-purple-300",
};

export default function StakeholderMap({ stakeholders }: Props) {
  const economicBuyer = stakeholders.find((s) => s.buyer_role === "economic_buyer");
  const otherStakeholders = stakeholders.filter((s) => s.buyer_role !== "economic_buyer");

  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold mb-6">Buying Committee</h2>

      {!economicBuyer && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-yellow-800 text-sm">⚠ No economic buyer identified. Add decision-maker to committee.</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Economic Buyer - Featured */}
        {economicBuyer && (
          <div className="mb-6 p-4 border-2 border-red-300 rounded-lg bg-gradient-to-r from-red-50 to-transparent">
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-bold text-lg">{economicBuyer.name}</h3>
                  <Badge className={ROLE_COLORS.economic_buyer}>Economic Buyer</Badge>
                </div>
                <p className="text-sm text-gray-600">{economicBuyer.title}</p>
                <p className="text-sm text-blue-600 mt-1">{economicBuyer.email}</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-red-600">
                  {Math.round(economicBuyer.engagement_score)}%
                </div>
                <p className="text-xs text-gray-500">Engagement</p>
              </div>
            </div>
            <div className="mt-4 flex gap-4 text-sm">
              <div>
                <span className="text-gray-600">Emails Opened:</span>
                <span className="font-medium ml-1">{economicBuyer.email_open_count}</span>
              </div>
              <div>
                <span className="text-gray-600">Meetings:</span>
                <span className="font-medium ml-1">{economicBuyer.meeting_count}</span>
              </div>
              {economicBuyer.last_activity && (
                <div>
                  <span className="text-gray-600">Last Active:</span>
                  <span className="font-medium ml-1">{new Date(economicBuyer.last_activity).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Other Stakeholders */}
        {otherStakeholders.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Other Stakeholders</h3>
            <div className="space-y-2">
              {otherStakeholders.map((stakeholder) => (
                <div
                  key={stakeholder.person_id}
                  className={`p-3 border rounded flex justify-between items-center ${ROLE_COLORS[stakeholder.buyer_role] || "bg-gray-100 text-gray-800"}`}
                >
                  <div>
                    <p className="font-medium">{stakeholder.name}</p>
                    <p className="text-xs opacity-75">{stakeholder.title}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{Math.round(stakeholder.engagement_score)}%</p>
                    <Badge variant="outline" className="mt-1 text-xs">
                      {stakeholder.buyer_role.replace("_", " ")}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {stakeholders.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No stakeholders identified yet.</p>
          </div>
        )}
      </div>
    </Card>
  );
}
