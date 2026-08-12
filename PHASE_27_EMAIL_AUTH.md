# Phase 27 - Email Verification & Account Approval System

**Part of Phase 27 Onboarding**  
**Timeline**: Week 1-2 (parallel with main Phase 27)  
**Team**: 1 backend + 1 frontend  
**Features**:
- Email verification on signup
- Account approval workflow (admin/manager approval)
- Approval notifications via email

---

## 1. DATABASE SCHEMA

### New Tables

```sql
-- ============================================================
-- SCHEMA: auth (or extend public schema)
-- ============================================================

-- Email verification tokens
CREATE TABLE email_verification_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  token VARCHAR(255) UNIQUE NOT NULL,
  
  -- Token lifecycle
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours',
  verified_at TIMESTAMP,
  
  -- Status
  is_verified BOOLEAN DEFAULT FALSE,
  verification_attempts INT DEFAULT 0,
  
  CONSTRAINT fk_user FOREIGN KEY (user_id) 
    REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_email_verification_token ON email_verification_tokens(token);
CREATE INDEX idx_email_verification_user ON email_verification_tokens(user_id);
CREATE INDEX idx_email_verification_email ON email_verification_tokens(email);

-- Account approval workflow
CREATE TABLE account_approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(255) NOT NULL,
  
  -- User details captured at request
  email VARCHAR(255) NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  company VARCHAR(255),
  role VARCHAR(255),
  
  -- Approval chain
  requested_at TIMESTAMP DEFAULT NOW(),
  requested_by VARCHAR(255),  -- Usually the user themselves
  approval_status VARCHAR(50),  -- pending, approved, rejected
  approved_by VARCHAR(255),  -- Admin/manager who approved
  approved_at TIMESTAMP,
  
  -- Notes
  approval_notes TEXT,
  rejection_reason TEXT,
  
  -- Auto-approval rules (optional)
  auto_approved BOOLEAN DEFAULT FALSE,
  auto_approval_rule VARCHAR(50),  -- company_whitelist, domain_whitelist, etc
  
  CONSTRAINT fk_user FOREIGN KEY (user_id) 
    REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_approvals_user ON account_approvals(user_id);
CREATE INDEX idx_approvals_status ON account_approvals(approval_status);
CREATE INDEX idx_approvals_requested_at ON account_approvals(requested_at DESC);

-- Approval audit log
CREATE TABLE approval_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  approval_id UUID NOT NULL,
  action VARCHAR(50),  -- requested, approved, rejected, escalated
  actor_id VARCHAR(255),  -- Who took action (admin)
  notes TEXT,
  action_timestamp TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_approval FOREIGN KEY (approval_id)
    REFERENCES account_approvals(id) ON DELETE CASCADE
);

CREATE INDEX idx_audit_approval ON approval_audit_log(approval_id);

-- Email templates for notifications
CREATE TABLE email_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_name VARCHAR(255) UNIQUE NOT NULL,  -- verification, approval_approved, approval_rejected, etc
  subject VARCHAR(255),
  body TEXT,  -- HTML template with {{placeholders}}
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);

INSERT INTO email_templates (template_name, subject, body) VALUES
('email_verification', 
 'Verify your SellIA email address',
 '<h2>Welcome to SellIA!</h2><p>Click link below to verify: {{verification_url}}</p><p>Link expires in 24 hours.</p>'),

('approval_requested',
 'New SellIA account approval needed',
 '<p>New user: {{full_name}} ({{email}})</p><p>Company: {{company}}</p><p>Action: <a href="{{approval_url}}">Review & Approve</a></p>'),

('approval_approved',
 'Your SellIA account is approved!',
 '<h2>Welcome to SellIA!</h2><p>Hi {{full_name}},</p><p>Your account has been approved. <a href="{{login_url}}">Log in here</a></p>'),

('approval_rejected',
 'SellIA account approval - update needed',
 '<p>Hi {{full_name}},</p><p>Your account needs review. Reason: {{rejection_reason}}</p><p>Contact: {{support_email}}</p>');

CREATE INDEX idx_email_templates_name ON email_templates(template_name);
```

---

## 2. BACKEND IMPLEMENTATION

### Service: EmailAuthManager

**File**: `backend/app/domains/auth/email_auth.py` (300 lines)

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import uuid
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models import User
from backend.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@dataclass
class EmailVerificationResult:
    """Result of email verification attempt."""
    success: bool
    user_id: str
    email: str
    message: str
    error_code: Optional[str] = None

@dataclass
class ApprovalRequest:
    """Account approval request."""
    user_id: str
    email: str
    full_name: str
    company: Optional[str]
    role: Optional[str]
    auto_approved: bool

class EmailAuthManager:
    """Manage email verification & account approval workflows."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    # ============================================================
    # EMAIL VERIFICATION
    # ============================================================
    
    async def create_verification_token(
        self,
        user_id: str,
        email: str
    ) -> str:
        """Generate verification token & send email."""
        
        # 1. Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # 2. Store token
        verification = EmailVerificationToken(
            user_id=user_id,
            email=email,
            token=token,
            expires_at=expires_at,
            is_verified=False
        )
        self.db.add(verification)
        self.db.commit()
        
        # 3. Send verification email (async task)
        send_verification_email.delay(
            user_id=user_id,
            email=email,
            token=token,
            verification_url=f"https://app.sellia.com/verify-email?token={token}"
        )
        
        logger.info(f"Verification token created for user {user_id}")
        return token
    
    async def verify_email_token(
        self,
        token: str
    ) -> EmailVerificationResult:
        """Verify email token and mark as verified."""
        
        # 1. Find token
        query = select(EmailVerificationToken).where(
            (EmailVerificationToken.token == token) &
            (EmailVerificationToken.is_verified == False)
        )
        verification = self.db.execute(query).scalar()
        
        if not verification:
            return EmailVerificationResult(
                success=False,
                user_id="",
                email="",
                message="Token not found or already verified",
                error_code="TOKEN_NOT_FOUND"
            )
        
        # 2. Check expiration
        if datetime.utcnow() > verification.expires_at:
            return EmailVerificationResult(
                success=False,
                user_id=verification.user_id,
                email=verification.email,
                message="Token expired",
                error_code="TOKEN_EXPIRED"
            )
        
        # 3. Mark as verified
        verification.is_verified = True
        verification.verified_at = datetime.utcnow()
        self.db.add(verification)
        
        # 4. Update user email_verified flag
        user = self.db.query(User).filter(User.id == verification.user_id).first()
        if user:
            user.email_verified = True
            user.verified_at = datetime.utcnow()
            self.db.add(user)
        
        self.db.commit()
        
        logger.info(f"Email verified for user {verification.user_id}")
        
        return EmailVerificationResult(
            success=True,
            user_id=verification.user_id,
            email=verification.email,
            message="Email verified successfully"
        )
    
    # ============================================================
    # ACCOUNT APPROVAL
    # ============================================================
    
    async def request_account_approval(
        self,
        user_id: str,
        email: str,
        full_name: str,
        company: Optional[str] = None,
        role: Optional[str] = None
    ) -> ApprovalRequest:
        """Create account approval request."""
        
        # 1. Check for auto-approval
        auto_approved = await self._check_auto_approval(email, company)
        
        # 2. Create approval record
        approval = AccountApproval(
            user_id=user_id,
            email=email,
            full_name=full_name,
            company=company,
            role=role,
            approval_status="approved" if auto_approved else "pending",
            approved_at=datetime.utcnow() if auto_approved else None,
            auto_approved=auto_approved,
            requested_by=user_id
        )
        self.db.add(approval)
        self.db.commit()
        
        # 3. Notify admins if pending
        if not auto_approved:
            notify_admins_approval_pending.delay(
                approval_id=str(approval.id),
                user_email=email,
                user_name=full_name,
                company=company
            )
        else:
            # Send approval email immediately
            send_approval_email.delay(
                user_id=user_id,
                email=email,
                full_name=full_name,
                approved=True
            )
            # Update user status
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.account_approved = True
                user.approval_status = "approved"
                self.db.add(user)
                self.db.commit()
        
        logger.info(f"Approval request created for {email} (auto={auto_approved})")
        
        return ApprovalRequest(
            user_id=user_id,
            email=email,
            full_name=full_name,
            company=company,
            role=role,
            auto_approved=auto_approved
        )
    
    async def approve_account(
        self,
        approval_id: str,
        admin_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Approve account (admin action)."""
        
        # 1. Get approval request
        approval = self.db.query(AccountApproval).filter(
            AccountApproval.id == approval_id
        ).first()
        
        if not approval or approval.approval_status != "pending":
            return False
        
        # 2. Update approval
        approval.approval_status = "approved"
        approval.approved_by = admin_id
        approval.approved_at = datetime.utcnow()
        approval.approval_notes = notes
        self.db.add(approval)
        
        # 3. Log audit
        audit = ApprovalAuditLog(
            approval_id=approval_id,
            action="approved",
            actor_id=admin_id,
            notes=notes
        )
        self.db.add(audit)
        
        # 4. Update user status
        user = self.db.query(User).filter(User.id == approval.user_id).first()
        if user:
            user.account_approved = True
            user.approval_status = "approved"
            self.db.add(user)
        
        self.db.commit()
        
        # 5. Send approval email
        send_approval_email.delay(
            user_id=approval.user_id,
            email=approval.email,
            full_name=approval.full_name,
            approved=True
        )
        
        logger.info(f"Account approved: {approval.email} (by {admin_id})")
        return True
    
    async def reject_account(
        self,
        approval_id: str,
        admin_id: str,
        rejection_reason: str
    ) -> bool:
        """Reject account (admin action)."""
        
        # Similar to approve, but with rejection_reason
        approval = self.db.query(AccountApproval).filter(
            AccountApproval.id == approval_id
        ).first()
        
        if not approval or approval.approval_status != "pending":
            return False
        
        approval.approval_status = "rejected"
        approval.approved_by = admin_id
        approval.approved_at = datetime.utcnow()
        approval.rejection_reason = rejection_reason
        self.db.add(approval)
        
        audit = ApprovalAuditLog(
            approval_id=approval_id,
            action="rejected",
            actor_id=admin_id,
            notes=rejection_reason
        )
        self.db.add(audit)
        self.db.commit()
        
        # Send rejection email
        send_rejection_email.delay(
            user_id=approval.user_id,
            email=approval.email,
            full_name=approval.full_name,
            rejection_reason=rejection_reason
        )
        
        return True
    
    async def _check_auto_approval(
        self,
        email: str,
        company: Optional[str]
    ) -> bool:
        """Check if should auto-approve based on rules."""
        # TODO: Implement auto-approval logic (whitelist, domain, etc)
        # For now, all require manual approval
        return False


# ============================================================
# CELERY TASKS - Email Sending
# ============================================================

@celery_app.task(bind=True, max_retries=3)
def send_verification_email(
    self,
    user_id: str,
    email: str,
    token: str,
    verification_url: str
):
    """Send verification email to user."""
    try:
        # 1. Get email template
        template = db.query(EmailTemplate).filter(
            EmailTemplate.template_name == "email_verification"
        ).first()
        
        # 2. Render template
        body = template.body.replace("{{verification_url}}", verification_url)
        
        # 3. Send email (using your email provider - SendGrid, AWS SES, etc)
        send_email(
            to_email=email,
            subject=template.subject,
            body=body,
            html=True
        )
        
        logger.info(f"Verification email sent to {email}")
        return {"status": "sent", "email": email}
        
    except Exception as exc:
        logger.error(f"Failed to send verification email: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def notify_admins_approval_pending(
    self,
    approval_id: str,
    user_email: str,
    user_name: str,
    company: Optional[str]
):
    """Notify admins of pending approval."""
    try:
        # 1. Get email template
        template = db.query(EmailTemplate).filter(
            EmailTemplate.template_name == "approval_requested"
        ).first()
        
        # 2. Get admin emails from config/db
        admin_emails = get_admin_emails()  # Your admin list
        
        # 3. Render & send to each admin
        for admin_email in admin_emails:
            body = template.body
            body = body.replace("{{full_name}}", user_name)
            body = body.replace("{{email}}", user_email)
            body = body.replace("{{company}}", company or "N/A")
            body = body.replace("{{approval_url}}", 
                f"https://app.sellia.com/admin/approvals/{approval_id}")
            
            send_email(
                to_email=admin_email,
                subject=template.subject,
                body=body,
                html=True
            )
        
        logger.info(f"Admin notification sent for approval {approval_id}")
        
    except Exception as exc:
        logger.error(f"Failed to notify admins: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_approval_email(
    self,
    user_id: str,
    email: str,
    full_name: str,
    approved: bool
):
    """Send approval/rejection notification."""
    try:
        template_name = "approval_approved" if approved else "approval_rejected"
        template = db.query(EmailTemplate).filter(
            EmailTemplate.template_name == template_name
        ).first()
        
        body = template.body.replace("{{full_name}}", full_name)
        body = body.replace("{{login_url}}", "https://app.sellia.com/login")
        
        send_email(
            to_email=email,
            subject=template.subject,
            body=body,
            html=True
        )
        
        logger.info(f"Approval email sent to {email}")
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_rejection_email(
    self,
    user_id: str,
    email: str,
    full_name: str,
    rejection_reason: str
):
    """Send rejection notification."""
    try:
        template = db.query(EmailTemplate).filter(
            EmailTemplate.template_name == "approval_rejected"
        ).first()
        
        body = template.body.replace("{{full_name}}", full_name)
        body = body.replace("{{rejection_reason}}", rejection_reason)
        body = body.replace("{{support_email}}", "support@sellia.com")
        
        send_email(
            to_email=email,
            subject=template.subject,
            body=body,
            html=True
        )
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

---

## 3. API ENDPOINTS

**File**: `backend/app/api/v1/email_auth.py` (200 lines)

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from backend.app.domains.auth.email_auth import EmailAuthManager

router = APIRouter(prefix="/api/v1/auth", tags=["email-auth"])

# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class EmailVerificationRequest(BaseModel):
    token: str

class EmailVerificationResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    error_code: Optional[str] = None

class ApprovalRequestBody(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str
    company: Optional[str] = None
    role: Optional[str] = None

class ApprovalResponse(BaseModel):
    success: bool
    user_id: str
    auto_approved: bool
    message: str

class AdminApprovalAction(BaseModel):
    approval_id: str
    action: str  # "approve" or "reject"
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None

# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    request: EmailVerificationRequest,
    email_auth: EmailAuthManager = Depends(get_email_auth_manager)
):
    """Verify email with token."""
    result = await email_auth.verify_email_token(request.token)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return EmailVerificationResponse(
        success=True,
        message=result.message,
        user_id=result.user_id
    )

@router.post("/request-approval", response_model=ApprovalResponse)
async def request_approval(
    request: ApprovalRequestBody,
    email_auth: EmailAuthManager = Depends(get_email_auth_manager)
):
    """Request account approval after email verification."""
    result = await email_auth.request_account_approval(
        user_id=request.user_id,
        email=request.email,
        full_name=request.full_name,
        company=request.company,
        role=request.role
    )
    
    return ApprovalResponse(
        success=True,
        user_id=result.user_id,
        auto_approved=result.auto_approved,
        message="Approval request submitted" if not result.auto_approved else "Account auto-approved!"
    )

@router.post("/admin/approve-account")
async def admin_approve_account(
    request: AdminApprovalAction,
    current_user = Depends(verify_admin_token),  # Only admins
    email_auth: EmailAuthManager = Depends(get_email_auth_manager)
):
    """Admin action: approve or reject account."""
    
    if request.action == "approve":
        success = await email_auth.approve_account(
            approval_id=request.approval_id,
            admin_id=current_user.id,
            notes=request.notes
        )
    elif request.action == "reject":
        success = await email_auth.reject_account(
            approval_id=request.approval_id,
            admin_id=current_user.id,
            rejection_reason=request.rejection_reason or "No reason provided"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    if not success:
        raise HTTPException(status_code=400, detail="Approval not found or already processed")
    
    return {"success": True, "action": request.action}

@router.get("/admin/pending-approvals")
async def get_pending_approvals(
    current_user = Depends(verify_admin_token),  # Only admins
):
    """List pending account approvals."""
    db = Depends(get_db)
    
    approvals = db.query(AccountApproval).filter(
        AccountApproval.approval_status == "pending"
    ).order_by(AccountApproval.requested_at.desc()).all()
    
    return [
        {
            "id": a.id,
            "email": a.email,
            "full_name": a.full_name,
            "company": a.company,
            "role": a.role,
            "requested_at": a.requested_at
        }
        for a in approvals
    ]
```

---

## 4. FRONTEND IMPLEMENTATION

### Email Verification Flow

**File**: `frontend/src/pages/verify-email.tsx`

```typescript
"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
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
          setMessage("Email verified! Redirecting to next step...");
          setTimeout(() => router.push("/signup/approval"), 2000);
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
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
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
            <Button 
              onClick={() => router.push("/signup")}
              className="w-full"
            >
              Back to Signup
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
```

### Account Approval Status Page

**File**: `frontend/src/pages/approval-status.tsx`

```typescript
"use client";

import React, { useEffect, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type ApprovalStatus = "pending" | "approved" | "rejected";

export default function ApprovalStatusPage() {
  const [status, setStatus] = useState<ApprovalStatus>("pending");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const checkApprovalStatus = async () => {
      const userId = localStorage.getItem("userId");
      
      const res = await fetch(`/api/v1/auth/approval-status/${userId}`);
      const data = await res.json();
      
      setStatus(data.approval_status);
      
      if (data.approval_status === "approved") {
        setMessage("Your account has been approved! You can now log in.");
      } else if (data.approval_status === "rejected") {
        setMessage(`Your account was rejected: ${data.rejection_reason}`);
      } else {
        setMessage("Your account is pending approval. We'll notify you via email once approved.");
      }
    };

    const interval = setInterval(checkApprovalStatus, 30000); // Check every 30s
    checkApprovalStatus(); // Check immediately

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full">
        <h1 className="text-2xl font-bold mb-6 text-center">Account Status</h1>

        {status === "pending" && (
          <Alert className="bg-blue-50 border-blue-200">
            <AlertDescription className="text-blue-800">
              ⏳ {message}
            </AlertDescription>
          </Alert>
        )}

        {status === "approved" && (
          <div>
            <Alert className="bg-green-50 border-green-200 mb-4">
              <AlertDescription className="text-green-800">
                ✓ {message}
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
                ✗ {message}
              </AlertDescription>
            </Alert>
            <Button href="/contact-support" className="w-full">
              Contact Support
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
```

### Admin Approval Dashboard

**File**: `frontend/src/components/Admin/ApprovalQueue.tsx`

```typescript
"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface PendingApproval {
  id: string;
  email: string;
  full_name: string;
  company?: string;
  role?: string;
  requested_at: string;
}

export default function ApprovalQueue() {
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPendingApprovals();
  }, []);

  const fetchPendingApprovals = async () => {
    const res = await fetch("/api/v1/auth/admin/pending-approvals");
    const data = await res.json();
    setApprovals(data);
    setLoading(false);
  };

  const handleApprove = async (approvalId: string, notes?: string) => {
    const res = await fetch("/api/v1/auth/admin/approve-account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        approval_id: approvalId,
        action: "approve",
        notes,
      }),
    });

    if (res.ok) {
      setApprovals(approvals.filter(a => a.id !== approvalId));
    }
  };

  const handleReject = async (approvalId: string, reason: string) => {
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
      setApprovals(approvals.filter(a => a.id !== approvalId));
    }
  };

  if (loading) return <div>Loading approvals...</div>;
  if (approvals.length === 0) return <div className="text-gray-600">No pending approvals</div>;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Pending Approvals ({approvals.length})</h2>
      
      {approvals.map(approval => (
        <Card key={approval.id} className="p-4">
          <div className="flex justify-between items-start mb-3">
            <div>
              <h3 className="font-bold">{approval.full_name}</h3>
              <p className="text-sm text-gray-600">{approval.email}</p>
              {approval.company && <p className="text-sm text-gray-600">{approval.company}</p>}
            </div>
            <span className="text-xs text-gray-500">
              {new Date(approval.requested_at).toLocaleDateString()}
            </span>
          </div>
          
          <div className="flex gap-2">
            <Button 
              onClick={() => handleApprove(approval.id)}
              className="bg-green-600 hover:bg-green-700"
            >
              Approve
            </Button>
            <Button 
              onClick={() => handleReject(approval.id, "Not approved")}
              variant="destructive"
            >
              Reject
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
```

---

## 5. SIGNUP FLOW INTEGRATION

**Updated Signup Process**:

1. User enters email + password → Create user record
2. Trigger email verification → Send verification email
3. User clicks link → Email verified ✓
4. User enters company + role info
5. Request account approval → Wait for admin
6. Admin approves/rejects → User notified via email
7. User logs in ✓

---

## 6. DATABASE MIGRATION

**File**: `backend/migrations/versions/0032_email_auth_schema.py`

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime()),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verification_attempts', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_email_verification_token', 'email_verification_tokens', ['token'])
    op.create_index('idx_email_verification_user', 'email_verification_tokens', ['user_id'])
    
    # Similar for account_approvals, approval_audit_log, email_templates tables...

def downgrade():
    op.drop_table('email_verification_tokens')
    # etc...
```

---

## 7. TESTING

### Unit Tests

```python
# backend/tests/test_email_auth.py

@pytest.mark.asyncio
async def test_create_verification_token():
    """Test verification token generation."""
    manager = EmailAuthManager(db_session)
    token = await manager.create_verification_token("user1", "user@example.com")
    assert len(token) > 0

@pytest.mark.asyncio
async def test_verify_email_token():
    """Test email verification."""
    manager = EmailAuthManager(db_session)
    token = await manager.create_verification_token("user1", "user@example.com")
    result = await manager.verify_email_token(token)
    assert result.success == True

@pytest.mark.asyncio
async def test_request_account_approval():
    """Test approval workflow."""
    manager = EmailAuthManager(db_session)
    result = await manager.request_account_approval(
        user_id="user1",
        email="user@example.com",
        full_name="John Doe",
        company="Acme Corp"
    )
    assert result.user_id == "user1"
```

---

## 8. SUCCESS CRITERIA

- [ ] Email verification tokens generate & expire correctly
- [ ] Verification email sends on signup
- [ ] Account approval workflow functional (admin can approve/reject)
- [ ] Approval emails sent to users
- [ ] Pending approvals dashboard shows all pending requests
- [ ] Users cannot log in until email verified + account approved
- [ ] Audit log tracks all approval actions
