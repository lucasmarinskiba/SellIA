"""Email authentication & account approval service."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.email_auth import (
    EmailVerificationToken,
    AccountApproval,
    ApprovalAuditLog,
    EmailTemplate,
)
from backend.app.models.user import User
from backend.celery_app import celery_app

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

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # EMAIL VERIFICATION
    # ============================================================

    def create_verification_token(self, user_id: str, email: str) -> str:
        """Generate verification token & queue email."""

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        verification = EmailVerificationToken(
            user_id=user_id,
            email=email,
            token=token,
            expires_at=expires_at,
            is_verified=False,
        )
        self.db.add(verification)
        self.db.commit()

        verification_url = f"https://app.sellia.com/verify-email?token={token}"
        send_verification_email.delay(
            user_id=user_id, email=email, token=token, verification_url=verification_url
        )

        logger.info(f"Verification token created for user {user_id}")
        return token

    def verify_email_token(self, token: str) -> EmailVerificationResult:
        """Verify email token and mark as verified."""

        query = select(EmailVerificationToken).where(
            (EmailVerificationToken.token == token) & (EmailVerificationToken.is_verified == False)
        )
        verification = self.db.execute(query).scalar()

        if not verification:
            return EmailVerificationResult(
                success=False,
                user_id="",
                email="",
                message="Token not found or already verified",
                error_code="TOKEN_NOT_FOUND",
            )

        if datetime.utcnow() > verification.expires_at:
            return EmailVerificationResult(
                success=False,
                user_id=verification.user_id,
                email=verification.email,
                message="Token expired",
                error_code="TOKEN_EXPIRED",
            )

        verification.is_verified = True
        verification.verified_at = datetime.utcnow()
        self.db.add(verification)

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
            message="Email verified successfully",
        )

    # ============================================================
    # ACCOUNT APPROVAL
    # ============================================================

    def request_account_approval(
        self,
        user_id: str,
        email: str,
        full_name: str,
        company: Optional[str] = None,
        role: Optional[str] = None,
    ) -> ApprovalRequest:
        """Create account approval request."""

        auto_approved = self._check_auto_approval(email, company)

        approval = AccountApproval(
            user_id=user_id,
            email=email,
            full_name=full_name,
            company=company,
            role=role,
            approval_status="approved" if auto_approved else "pending",
            approved_at=datetime.utcnow() if auto_approved else None,
            auto_approved=auto_approved,
            requested_by=user_id,
        )
        self.db.add(approval)
        self.db.commit()

        if not auto_approved:
            notify_admins_approval_pending.delay(
                approval_id=str(approval.id),
                user_email=email,
                user_name=full_name,
                company=company or "",
            )
        else:
            send_approval_email.delay(
                user_id=user_id, email=email, full_name=full_name, approved=True
            )

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
            auto_approved=auto_approved,
        )

    def approve_account(self, approval_id: str, admin_id: str, notes: Optional[str] = None) -> bool:
        """Approve account (admin action)."""

        approval = self.db.query(AccountApproval).filter(AccountApproval.id == approval_id).first()

        if not approval or approval.approval_status != "pending":
            return False

        approval.approval_status = "approved"
        approval.approved_by = admin_id
        approval.approved_at = datetime.utcnow()
        approval.approval_notes = notes
        self.db.add(approval)

        audit = ApprovalAuditLog(approval_id=approval_id, action="approved", actor_id=admin_id, notes=notes)
        self.db.add(audit)

        user = self.db.query(User).filter(User.id == approval.user_id).first()
        if user:
            user.account_approved = True
            user.approval_status = "approved"
            self.db.add(user)

        self.db.commit()

        send_approval_email.delay(
            user_id=approval.user_id, email=approval.email, full_name=approval.full_name, approved=True
        )

        logger.info(f"Account approved: {approval.email} (by {admin_id})")
        return True

    def reject_account(self, approval_id: str, admin_id: str, rejection_reason: str) -> bool:
        """Reject account (admin action)."""

        approval = self.db.query(AccountApproval).filter(AccountApproval.id == approval_id).first()

        if not approval or approval.approval_status != "pending":
            return False

        approval.approval_status = "rejected"
        approval.approved_by = admin_id
        approval.approved_at = datetime.utcnow()
        approval.rejection_reason = rejection_reason
        self.db.add(approval)

        audit = ApprovalAuditLog(
            approval_id=approval_id, action="rejected", actor_id=admin_id, notes=rejection_reason
        )
        self.db.add(audit)
        self.db.commit()

        send_rejection_email.delay(
            user_id=approval.user_id,
            email=approval.email,
            full_name=approval.full_name,
            rejection_reason=rejection_reason,
        )

        return True

    def get_pending_approvals(self, limit: int = 100) -> List[dict]:
        """Get pending account approvals."""

        approvals = (
            self.db.query(AccountApproval)
            .filter(AccountApproval.approval_status == "pending")
            .order_by(AccountApproval.requested_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(a.id),
                "email": a.email,
                "full_name": a.full_name,
                "company": a.company,
                "role": a.role,
                "requested_at": a.requested_at.isoformat(),
            }
            for a in approvals
        ]

    def get_approval_status(self, user_id: str) -> Optional[dict]:
        """Get account approval status for user."""

        approval = (
            self.db.query(AccountApproval)
            .filter(AccountApproval.user_id == user_id)
            .order_by(AccountApproval.requested_at.desc())
            .first()
        )

        if not approval:
            return None

        return {
            "approval_status": approval.approval_status,
            "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
            "rejection_reason": approval.rejection_reason,
            "auto_approved": approval.auto_approved,
        }

    def _check_auto_approval(self, email: str, company: Optional[str]) -> bool:
        """Check if should auto-approve based on rules."""
        # TODO: Implement auto-approval logic
        return False


# ============================================================
# CELERY TASKS - Email Sending
# ============================================================


def get_email_template(template_name: str, db: Session) -> Optional[EmailTemplate]:
    """Get email template by name."""
    return db.query(EmailTemplate).filter(EmailTemplate.template_name == template_name).first()


def send_email(to_email: str, subject: str, body: str, html: bool = True) -> bool:
    """Send email using provider (SendGrid, AWS SES, etc)."""
    # TODO: Implement with your email provider
    logger.info(f"Email sent to {to_email}: {subject}")
    return True


@celery_app.task(bind=True, max_retries=3)
def send_verification_email(self, user_id: str, email: str, token: str, verification_url: str):
    """Send verification email to user."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        template = get_email_template("email_verification", db)

        if not template:
            logger.error("Email template not found: email_verification")
            return {"status": "error", "message": "Template not found"}

        body = template.body.replace("{{verification_url}}", verification_url)

        send_email(to_email=email, subject=template.subject, body=body, html=True)

        logger.info(f"Verification email sent to {email}")
        db.close()
        return {"status": "sent", "email": email}

    except Exception as exc:
        logger.error(f"Failed to send verification email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def notify_admins_approval_pending(self, approval_id: str, user_email: str, user_name: str, company: str):
    """Notify admins of pending approval."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        template = get_email_template("approval_requested", db)

        if not template:
            logger.error("Email template not found: approval_requested")
            return

        # Get admin emails (from config or db)
        admin_emails = ["admin@sellia.com"]  # TODO: Get from config

        for admin_email in admin_emails:
            body = template.body
            body = body.replace("{{full_name}}", user_name)
            body = body.replace("{{email}}", user_email)
            body = body.replace("{{company}}", company or "N/A")
            body = body.replace("{{approval_url}}", f"https://app.sellia.com/admin/approvals/{approval_id}")

            send_email(to_email=admin_email, subject=template.subject, body=body, html=True)

        logger.info(f"Admin notification sent for approval {approval_id}")
        db.close()

    except Exception as exc:
        logger.error(f"Failed to notify admins: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_approval_email(self, user_id: str, email: str, full_name: str, approved: bool):
    """Send approval notification."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        template_name = "approval_approved" if approved else "approval_rejected"
        template = get_email_template(template_name, db)

        if not template:
            logger.error(f"Email template not found: {template_name}")
            return

        body = template.body.replace("{{full_name}}", full_name)
        body = body.replace("{{login_url}}", "https://app.sellia.com/login")

        send_email(to_email=email, subject=template.subject, body=body, html=True)

        logger.info(f"Approval email sent to {email}")
        db.close()

    except Exception as exc:
        logger.error(f"Failed to send approval email: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_rejection_email(
    self, user_id: str, email: str, full_name: str, rejection_reason: str
):
    """Send rejection notification."""
    try:
        from backend.app.database import SessionLocal

        db = SessionLocal()
        template = get_email_template("approval_rejected", db)

        if not template:
            logger.error("Email template not found: approval_rejected")
            return

        body = template.body.replace("{{full_name}}", full_name)
        body = body.replace("{{rejection_reason}}", rejection_reason)
        body = body.replace("{{support_email}}", "support@sellia.com")

        send_email(to_email=email, subject=template.subject, body=body, html=True)

        logger.info(f"Rejection email sent to {email}")
        db.close()

    except Exception as exc:
        logger.error(f"Failed to send rejection email: {exc}")
        raise self.retry(exc=exc, countdown=60)
