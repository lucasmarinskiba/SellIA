"""Email authentication API endpoints."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.domains.auth.email_auth import EmailAuthManager
from backend.app.dependencies import get_current_user, verify_admin_token

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


class PendingApprovalItem(BaseModel):
    id: str
    email: str
    full_name: str
    company: Optional[str]
    role: Optional[str]
    requested_at: str


class ApprovalStatusResponse(BaseModel):
    approval_status: str  # pending, approved, rejected
    approved_at: Optional[str]
    rejection_reason: Optional[str]
    auto_approved: bool


# ============================================================
# ENDPOINTS
# ============================================================


@router.post("/verify-email", response_model=EmailVerificationResponse)
def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    """Verify email with token."""
    email_auth = EmailAuthManager(db)
    result = email_auth.verify_email_token(request.token)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return EmailVerificationResponse(
        success=True,
        message=result.message,
        user_id=result.user_id,
    )


@router.post("/request-approval", response_model=ApprovalResponse)
def request_approval(
    request: ApprovalRequestBody,
    db: Session = Depends(get_db),
):
    """Request account approval after email verification."""
    email_auth = EmailAuthManager(db)
    result = email_auth.request_account_approval(
        user_id=request.user_id,
        email=request.email,
        full_name=request.full_name,
        company=request.company,
        role=request.role,
    )

    message = "Approval request submitted" if not result.auto_approved else "Account auto-approved!"

    return ApprovalResponse(
        success=True,
        user_id=result.user_id,
        auto_approved=result.auto_approved,
        message=message,
    )


@router.get("/approval-status/{user_id}", response_model=ApprovalStatusResponse)
def get_approval_status(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get account approval status for user."""
    email_auth = EmailAuthManager(db)
    status = email_auth.get_approval_status(user_id)

    if not status:
        raise HTTPException(status_code=404, detail="No approval found for user")

    return ApprovalStatusResponse(**status)


@router.post("/admin/approve-account")
def admin_approve_account(
    request: AdminApprovalAction,
    current_user=Depends(verify_admin_token),
    db: Session = Depends(get_db),
):
    """Admin action: approve or reject account."""
    email_auth = EmailAuthManager(db)

    if request.action == "approve":
        success = email_auth.approve_account(
            approval_id=request.approval_id,
            admin_id=current_user.id,
            notes=request.notes,
        )
    elif request.action == "reject":
        success = email_auth.reject_account(
            approval_id=request.approval_id,
            admin_id=current_user.id,
            rejection_reason=request.rejection_reason or "No reason provided",
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    if not success:
        raise HTTPException(status_code=400, detail="Approval not found or already processed")

    return {"success": True, "action": request.action}


@router.get("/admin/pending-approvals", response_model=List[PendingApprovalItem])
def get_pending_approvals(
    current_user=Depends(verify_admin_token),
    db: Session = Depends(get_db),
):
    """List pending account approvals."""
    email_auth = EmailAuthManager(db)
    approvals = email_auth.get_pending_approvals()

    return [PendingApprovalItem(**a) for a in approvals]
