/**
 * Account Approval Request Page
 * User submits company info → request approval → wait for admin
 */

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function ApprovalRequestPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    full_name: "",
    company: "",
    role: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const userId = localStorage.getItem("userId");
      const userEmail = localStorage.getItem("userEmail");

      if (!userId || !userEmail) {
        setError("Session expired. Please sign up again.");
        setLoading(false);
        return;
      }

      const res = await fetch("/api/v1/auth/request-approval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          email: userEmail,
          full_name: formData.full_name,
          company: formData.company,
          role: formData.role,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setSuccess(true);
        localStorage.setItem("approvalSubmitted", "true");
        setTimeout(() => router.push("/signup/approval-status"), 2000);
      } else {
        setError(data.detail || "Failed to submit approval request");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full">
        <h1 className="text-2xl font-bold mb-2 text-center">Complete Your Profile</h1>
        <p className="text-gray-600 text-center mb-6">
          Help us approve your account faster by sharing these details.
        </p>

        {success && (
          <Alert className="bg-green-50 border-green-200 mb-6">
            <AlertDescription className="text-green-800">
              ✓ Approval request submitted! Redirecting...
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert className="bg-red-50 border-red-200 mb-6">
            <AlertDescription className="text-red-800">✗ {error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <Input
              type="text"
              placeholder="John Doe"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
            <Input
              type="text"
              placeholder="Acme Corp"
              value={formData.company}
              onChange={(e) => setFormData({ ...formData, company: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
            <Input
              type="text"
              placeholder="Sales Manager"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            />
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Submitting..." : "Request Approval"}
          </Button>
        </form>

        <p className="text-xs text-gray-500 text-center mt-4">
          Our team reviews approvals within 2-4 hours. You'll receive an email notification.
        </p>
      </div>
    </div>
  );
}
