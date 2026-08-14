/**
 * Admin Approval Queue Component
 * Lists pending account approvals
 * Allows admins to approve/reject with notes
 */

"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface PendingApproval {
  id: string;
  email: string;
  full_name: string;
  company?: string;
  role?: string;
  requested_at: string;
}

interface ProcessingState {
  [key: string]: "idle" | "approving" | "rejecting";
}

export default function ApprovalQueue() {
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [processingState, setProcessingState] = useState<ProcessingState>({});
  const [rejectionNotes, setRejectionNotes] = useState<{ [key: string]: string }>({});
  const [showRejectionForm, setShowRejectionForm] = useState<{ [key: string]: boolean }>({});

  useEffect(() => {
    fetchPendingApprovals();
    const interval = setInterval(fetchPendingApprovals, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchPendingApprovals = async () => {
    try {
      const res = await fetch("/api/v1/auth/admin/pending-approvals");

      if (res.ok) {
        const data = await res.json();
        setApprovals(data);
        setError("");
      } else {
        setError("Failed to load pending approvals");
      }
    } catch (error) {
      setError("Network error while loading approvals");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approvalId: string) => {
    setProcessingState({ ...processingState, [approvalId]: "approving" });

    try {
      const res = await fetch("/api/v1/auth/admin/approve-account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          approval_id: approvalId,
          action: "approve",
        }),
      });

      if (res.ok) {
        setApprovals(approvals.filter((a) => a.id !== approvalId));
      } else {
        setError("Failed to approve account");
      }
    } catch (error) {
      setError("Network error while approving account");
    } finally {
      setProcessingState({ ...processingState, [approvalId]: "idle" });
    }
  };

  const handleReject = async (approvalId: string) => {
    const reason = rejectionNotes[approvalId] || "Not approved";

    setProcessingState({ ...processingState, [approvalId]: "rejecting" });

    try {
      const res = await fetch("/api/v1/auth/admin/approve-account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          approval_id: approvalId,
          action: "reject",
          rejection_reason: reason,
        }),
      });

      if (res.ok) {
        setApprovals(approvals.filter((a) => a.id !== approvalId));
        setShowRejectionForm({ ...showRejectionForm, [approvalId]: false });
        setRejectionNotes({ ...rejectionNotes, [approvalId]: "" });
      } else {
        setError("Failed to reject account");
      }
    } catch (error) {
      setError("Network error while rejecting account");
    } finally {
      setProcessingState({ ...processingState, [approvalId]: "idle" });
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2" />
        <p className="text-gray-600">Loading approvals...</p>
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

  if (approvals.length === 0) {
    return (
      <div className="text-center py-8 text-gray-600">
        <p className="text-lg">No pending approvals</p>
        <p className="text-sm text-gray-500">All accounts have been reviewed</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Pending Account Approvals</h2>
        <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
          {approvals.length}
        </span>
      </div>

      {approvals.map((approval) => (
        <Card key={approval.id} className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-xs text-gray-500 uppercase">Name</p>
              <p className="text-lg font-semibold">{approval.full_name}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Email</p>
              <p className="text-sm text-blue-600 break-all">{approval.email}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Company</p>
              <p className="text-sm">{approval.company || "Not provided"}</p>
            </div>
          </div>

          {approval.role && (
            <div className="mb-4">
              <p className="text-xs text-gray-500 uppercase">Role</p>
              <p className="text-sm">{approval.role}</p>
            </div>
          )}

          <div className="mb-4">
            <p className="text-xs text-gray-500 uppercase">Requested</p>
            <p className="text-sm text-gray-600">
              {new Date(approval.requested_at).toLocaleString()}
            </p>
          </div>

          {showRejectionForm[approval.id] ? (
            <div className="bg-red-50 border border-red-200 rounded p-4 mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rejection Reason
              </label>
              <Input
                type="text"
                placeholder="e.g., Insufficient company information"
                value={rejectionNotes[approval.id] || ""}
                onChange={(e) =>
                  setRejectionNotes({
                    ...rejectionNotes,
                    [approval.id]: e.target.value,
                  })
                }
                className="mb-3"
              />
              <div className="flex gap-2">
                <Button
                  onClick={() => handleReject(approval.id)}
                  disabled={processingState[approval.id] === "rejecting"}
                  className="bg-red-600 hover:bg-red-700 flex-1"
                >
                  {processingState[approval.id] === "rejecting" ? "Rejecting..." : "Confirm Rejection"}
                </Button>
                <Button
                  onClick={() => setShowRejectionForm({ ...showRejectionForm, [approval.id]: false })}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex gap-2">
              <Button
                onClick={() => handleApprove(approval.id)}
                disabled={processingState[approval.id] !== "idle"}
                className="bg-green-600 hover:bg-green-700 flex-1"
              >
                {processingState[approval.id] === "approving" ? "Approving..." : "✓ Approve"}
              </Button>
              <Button
                onClick={() => setShowRejectionForm({ ...showRejectionForm, [approval.id]: true })}
                disabled={processingState[approval.id] !== "idle"}
                variant="destructive"
                className="flex-1"
              >
                ✗ Reject
              </Button>
            </div>
          )}
        </Card>
      ))}
    </div>
  );
}

