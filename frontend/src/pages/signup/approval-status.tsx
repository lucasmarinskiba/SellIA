/**
 * Account Approval Status Page
 * Shows approval status (pending/approved/rejected)
 * Polls for status updates
 */

"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type ApprovalStatus = "pending" | "approved" | "rejected" | "loading";

interface StatusData {
  approval_status: ApprovalStatus;
  rejection_reason?: string;
  approved_at?: string;
  auto_approved: boolean;
}

export default function ApprovalStatusPage() {
  const router = useRouter();
  const [status, setStatus] = useState<ApprovalStatus>("loading");
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [checkCount, setCheckCount] = useState(0);

  useEffect(() => {
    const checkApprovalStatus = async () => {
      const userId = localStorage.getItem("userId");

      if (!userId) {
        router.push("/signup");
        return;
      }

      try {
        const res = await fetch(`/api/v1/auth/approval-status/${userId}`);

        if (res.ok) {
          const data = await res.json();
          setStatusData(data);
          setStatus(data.approval_status);

          if (data.approval_status === "approved") {
            localStorage.setItem("accountApproved", "true");
          }
        }
      } catch (error) {
        console.error("Error checking approval status:", error);
      }

      setCheckCount((c) => c + 1);
    };

    checkApprovalStatus();

    const interval = setInterval(checkApprovalStatus, 30000);
    return () => clearInterval(interval);
  }, [router]);

  useEffect(() => {
    if (status === "approved") {
      setTimeout(() => router.push("/login"), 2000);
    }
  }, [status, router]);

  const getPendingMessage = () => {
    if (checkCount === 0) {
      return "Submitting your approval request...";
    }
    if (checkCount < 4) {
      return "Your account is being reviewed. This usually takes 2-4 hours.";
    }
    return "Still reviewing your account. We'll email you as soon as you're approved!";
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full">
        <h1 className="text-2xl font-bold mb-6 text-center">Account Status</h1>

        {status === "loading" && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">{getPendingMessage()}</p>
          </div>
        )}

        {status === "pending" && (
          <Alert className="bg-blue-50 border-blue-200">
            <AlertDescription className="text-blue-800">
              ⏳ {getPendingMessage()}
            </AlertDescription>
          </Alert>
        )}

        {status === "approved" && (
          <div>
            <Alert className="bg-green-50 border-green-200 mb-4">
              <AlertDescription className="text-green-800">
                ✓ Your account has been approved! Redirecting to login...
              </AlertDescription>
            </Alert>
            <Button href="/login" className="w-full">
              Go to Login
            </Button>
          </div>
        )}

        {status === "rejected" && (
          <div>
            <Alert className="bg-red-50 border-red-200 mb-4">
              <AlertDescription className="text-red-800">
                ✗ Your account approval was rejected
                {statusData?.rejection_reason && `: ${statusData.rejection_reason}`}
              </AlertDescription>
            </Alert>
            <Button href="/contact-support" className="w-full mb-2">
              Contact Support
            </Button>
            <Button href="/signup" variant="outline" className="w-full">
              Try Again
            </Button>
          </div>
        )}

        {status === "pending" && (
          <div className="mt-6 pt-6 border-t">
            <p className="text-xs text-gray-500 mb-3">
              Check your email for updates. We'll notify you immediately when approved.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
