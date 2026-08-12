/**
 * Email Verification Page
 * User clicks verification link → verify token → redirect to approval request
 */

"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type VerificationStatus = "loading" | "success" | "error";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<VerificationStatus>("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get("token");

      if (!token) {
        setStatus("error");
        setMessage("No verification token provided");
        return;
      }

      try {
        const res = await fetch("/api/v1/auth/verify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });

        const data = await res.json();

        if (res.ok) {
          setStatus("success");
          setMessage("Email verified! Redirecting...");
          localStorage.setItem("userId", data.user_id);
          setTimeout(() => router.push("/signup/approval-request"), 2000);
        } else {
          setStatus("error");
          setMessage(data.detail || "Verification failed");
        }
      } catch (error) {
        setStatus("error");
        setMessage("Network error. Please try again.");
      }
    };

    verifyEmail();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full">
        <h1 className="text-2xl font-bold mb-6 text-center">Email Verification</h1>

        {status === "loading" && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">Verifying your email...</p>
          </div>
        )}

        {status === "success" && (
          <Alert className="bg-green-50 border-green-200">
            <AlertDescription className="text-green-800">✓ {message}</AlertDescription>
          </Alert>
        )}

        {status === "error" && (
          <div>
            <Alert className="bg-red-50 border-red-200 mb-4">
              <AlertDescription className="text-red-800">✗ {message}</AlertDescription>
            </Alert>
            <Button onClick={() => router.push("/signup")} className="w-full">
              Back to Signup
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
