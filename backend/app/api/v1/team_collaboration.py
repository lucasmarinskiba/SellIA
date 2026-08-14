"""Phase 26: Team Collaboration endpoints - Real-time deal collaboration."""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database import get_db
from backend.app.domains.enterprise.collaboration import (
    CollaborationManager,
    DealComment,
    ApprovalChain,
    Handoff,
    TeamNotification,
)

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


@router.post("/deals/{deal_id}/comments")
async def add_comment(
    deal_id: str,
    user_id: str = Query(...),
    user_name: str = Query(...),
    content: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Add comment to deal (broadcasts to team via WebSocket)."""
    comment = await CollaborationManager.add_comment(
        db=db,
        deal_id=deal_id,
        user_id=user_id,
        user_name=user_name,
        content=content,
    )
    return {
        "id": comment.id,
        "user_name": comment.user_name,
        "content": comment.content,
        "created_at": comment.created_at.isoformat(),
    }


@router.get("/deals/{deal_id}/comments")
async def list_comments(deal_id: str, limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    """Get all comments on deal."""
    stmt = (
        select(DealComment)
        .where(DealComment.deal_id == deal_id)
        .order_by(DealComment.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    comments = result.scalars().all()
    return {
        "deal_id": deal_id,
        "count": len(comments),
        "comments": [
            {
                "id": c.id,
                "user_name": c.user_name,
                "content": c.content,
                "created_at": c.created_at.isoformat(),
            }
            for c in reversed(comments)
        ],
    }


@router.post("/approvals/request")
async def request_approval(
    action_id: str = Query(...),
    action_type: str = Query(...),  # discount, escalation, etc
    requester_id: str = Query(...),
    requester_name: str = Query(...),
    approver_ids: list[str] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Request approval for action (discount, escalation, proposal, close)."""
    chain = await CollaborationManager.request_approval(
        db=db,
        action_id=action_id,
        action_type=action_type,
        requester_id=requester_id,
        requester_name=requester_name,
        approver_ids=approver_ids,
    )
    return {
        "approval_id": chain.id,
        "action_id": chain.action_id,
        "status": "pending",
        "approvers_count": len(approver_ids),
    }


@router.post("/approvals/{approval_id}/decide")
async def approve_action(
    approval_id: str,
    approver_id: str = Query(...),
    decision: str = Query(...),  # "approved" or "rejected"
    rejection_reason: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject action."""
    stmt = select(ApprovalChain).where(ApprovalChain.id == approval_id)
    result = await db.execute(stmt)
    chain = result.scalars().first()

    if not chain:
        raise HTTPException(status_code=404, detail="Approval not found")

    updated = await CollaborationManager.approve_action(
        db=db,
        action_id=chain.action_id,
        approver_id=approver_id,
        decision=decision,
        rejection_reason=rejection_reason,
    )

    return {
        "approval_id": approval_id,
        "status": updated.status,
        "decision_by": updated.decision_by,
        "decision_at": updated.decision_at.isoformat() if updated.decision_at else None,
    }


@router.get("/approvals/pending/{user_id}")
async def list_pending_approvals(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get pending approvals for user."""
    stmt = select(ApprovalChain).where(
        ApprovalChain.status == "pending",
        ApprovalChain.approval_steps.like(f"%{user_id}%"),
    )
    result = await db.execute(stmt)
    approvals = result.scalars().all()

    return {
        "user_id": user_id,
        "pending_count": len(approvals),
        "approvals": [
            {
                "id": a.id,
                "action_id": a.action_id,
                "action_type": a.action_type,
                "requester_name": a.requester_name,
                "created_at": a.created_at.isoformat(),
            }
            for a in approvals
        ],
    }


@router.post("/handoffs")
async def create_handoff(
    deal_id: str = Query(...),
    from_user_id: str = Query(...),
    from_user_name: str = Query(...),
    to_user_id: str = Query(...),
    to_user_name: str = Query(...),
    reason: str = Body(...),
    notes: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Pass deal to teammate."""
    handoff = await CollaborationManager.create_handoff(
        db=db,
        deal_id=deal_id,
        from_user_id=from_user_id,
        from_user_name=from_user_name,
        to_user_id=to_user_id,
        to_user_name=to_user_name,
        reason=reason,
        notes=notes,
    )
    return {
        "handoff_id": handoff.id,
        "deal_id": deal_id,
        "to_user": to_user_name,
        "status": "pending",
    }


@router.get("/handoffs/incoming/{user_id}")
async def list_incoming_handoffs(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get incoming handoffs (pending deals from teammates)."""
    stmt = select(Handoff).where(
        Handoff.to_user_id == user_id,
        Handoff.status == "pending",
    )
    result = await db.execute(stmt)
    handoffs = result.scalars().all()

    return {
        "user_id": user_id,
        "incoming_count": len(handoffs),
        "handoffs": [
            {
                "id": h.id,
                "deal_id": h.deal_id,
                "from_user": h.from_user_name,
                "reason": h.reason,
                "notes": h.notes,
                "created_at": h.created_at.isoformat(),
            }
            for h in handoffs
        ],
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, db: AsyncSession = Depends(get_db)):
    """Mark notification as read."""
    stmt = select(TeamNotification).where(TeamNotification.id == notification_id)
    result = await db.execute(stmt)
    notif = result.scalars().first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    await db.commit()
    return {"notification_id": notification_id, "is_read": True}


@router.get("/notifications/{user_id}")
async def list_notifications(
    user_id: str,
    unread_only: bool = Query(False),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    """Get user notifications (real-time collaboration updates)."""
    stmt = select(TeamNotification).where(TeamNotification.user_id == user_id)

    if unread_only:
        stmt = stmt.where(TeamNotification.is_read == False)

    stmt = stmt.order_by(TeamNotification.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    notifs = result.scalars().all()

    return {
        "user_id": user_id,
        "count": len(notifs),
        "unread_count": sum(1 for n in notifs if not n.is_read),
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifs
        ],
    }
