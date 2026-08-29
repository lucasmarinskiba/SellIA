/**
 * Voice Call Builder Component (Phase 29)
 * Initiate + manage AI voice calls with real-time transcript
 */

"use client";

import React, { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/Button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

interface CallState {
  callId: string;
  prospectId: string;
  dealId: string;
  status: "idle" | "calling" | "active" | "ended";
  transcript: Array<{ speaker: "prospect" | "ai"; text: string; time: string }>;
  outcome: string;
  meetingBooked: boolean;
  duration: number;
}

interface Props {
  dealId: string;
  prospectId: string;
  prospectName: string;
}

export default function VoiceCallBuilder({ dealId, prospectId, prospectName }: Props) {
  const [callState, setCallState] = useState<CallState>({
    callId: "",
    prospectId,
    dealId,
    status: "idle",
    transcript: [],
    outcome: "",
    meetingBooked: false,
    duration: 0,
  });

  const [playbook, setPlaybook] = useState<any>(null);
  const [error, setError] = useState("");
  const [callDuration, setCallDuration] = useState(0);

  // Poll call duration
  useEffect(() => {
    if (callState.status === "active") {
      const interval = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [callState.status]);

  const startCall = async () => {
    try {
      // 1. Get recommended playbook
      const pbRes = await fetch(`/api/v1/voice/playbooks/recommend/${dealId}`);
      const playbook = pbRes.ok ? await pbRes.json() : null;
      if (playbook) setPlaybook(playbook);

      // 2. Initiate call
      const res = await fetch("/api/v1/voice/initiate-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prospect_id: prospectId, deal_id: dealId }),
      });

      const data = await res.json();

      if (res.ok) {
        setCallState({
          ...callState,
          callId: data.call_id,
          status: "active",
          transcript: [{ speaker: "ai", text: data.script, time: new Date().toLocaleTimeString() }],
        });
        setError("");
      } else {
        setError(data.detail || "Failed to start call");
      }
    } catch (error) {
      setError("Network error starting call");
    }
  };

  const endCall = async () => {
    try {
      const res = await fetch("/api/v1/voice/call/end", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          call_id: callState.callId,
          outcome: callState.outcome || "unqualified",
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setCallState({
          ...callState,
          status: "ended",
          outcome: data.outcome,
          meetingBooked: data.meeting_booked,
          duration: data.duration,
        });
      }
    } catch (error) {
      setError("Error ending call");
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Voice Call</h1>
          <p className="text-gray-600">Calling {prospectName}</p>
        </div>
        <Badge className={callState.status === "active" ? "bg-red-100 text-red-800 animate-pulse" : ""}>
          {callState.status.toUpperCase()}
        </Badge>
      </div>

      {/* Playbook Recommendation */}
      {playbook && callState.status === "active" && (
        <Card className="p-4 bg-blue-50 border-blue-200">
          <p className="text-sm font-semibold text-blue-900 mb-2">📚 Recommended Playbook</p>
          <p className="text-lg font-bold text-blue-900 mb-1">{playbook.name}</p>
          <div className="flex gap-4 text-sm text-blue-800">
            <span>Win Rate: {Math.round(playbook.win_rate * 100)}%</span>
            <span>Next: {playbook.next_step}</span>
          </div>
        </Card>
      )}

      {/* Error Alert */}
      {error && (
        <Alert className="bg-red-50 border-red-200">
          <AlertDescription className="text-red-800">✗ {error}</AlertDescription>
        </Alert>
      )}

      {/* Call Controls */}
      <div className="flex gap-4">
        {callState.status === "idle" && (
          <Button onClick={startCall} className="bg-green-600 hover:bg-green-700 text-white px-8">
            📞 Start Call
          </Button>
        )}

        {callState.status === "active" && (
          <div className="flex gap-2">
            <div className="px-4 py-2 bg-red-100 text-red-800 rounded font-mono text-lg">
              {formatTime(callDuration)}
            </div>
            <Button onClick={endCall} className="bg-red-600 hover:bg-red-700 text-white">
              End Call
            </Button>
          </div>
        )}
      </div>

      {/* Live Transcript */}
      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Live Transcript</h2>

        <div className="space-y-3 max-h-96 overflow-y-auto">
          {callState.transcript.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No conversation yet. Start the call to begin.</p>
          ) : (
            callState.transcript.map((turn, idx) => (
              <div
                key={idx}
                className={`p-3 rounded ${
                  turn.speaker === "ai"
                    ? "bg-blue-50 border-l-4 border-blue-400"
                    : "bg-green-50 border-l-4 border-green-400"
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="font-semibold text-sm">
                    {turn.speaker === "ai" ? "🤖 AI Agent" : "👤 Prospect"}
                  </span>
                  <span className="text-xs text-gray-500">{turn.time}</span>
                </div>
                <p className="text-sm text-gray-700">{turn.text}</p>
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Call Summary */}
      {callState.status === "ended" && (
        <Card className="p-6 bg-gray-50">
          <h2 className="text-lg font-bold mb-4">Call Summary</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Duration</p>
              <p className="text-2xl font-bold">{formatTime(callState.duration)}</p>
            </div>

            <div>
              <p className="text-sm text-gray-600">Outcome</p>
              <Badge
                className={
                  callState.meetingBooked
                    ? "bg-green-100 text-green-800 text-lg py-2"
                    : "bg-yellow-100 text-yellow-800 text-lg py-2"
                }
              >
                {callState.meetingBooked ? "✓ Meeting Booked" : "Qualified"}
              </Badge>
            </div>
          </div>

          <div className="mt-6">
            <Button onClick={startCall} className="w-full bg-green-600 hover:bg-green-700">
              📞 Make Another Call
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

