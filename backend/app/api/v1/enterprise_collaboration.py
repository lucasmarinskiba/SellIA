from uuid import UUID

from fastapi import APIRouter, Query, Body, WebSocket, Depends, HTTPException
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.crm.models import Deal
from app.domains.enterprise.collaboration import CollaborationManager, CollaborationActionEnum

router = APIRouter(tags=["collaboration"])
collab_manager = CollaborationManager()


async def _verify_deal_access(deal_id: str, user: User, db: AsyncSession) -> Deal:
    """Look up the deal and verify it belongs to a business the caller owns.

    None of the routes below checked this before -- deal_id was a bare path/
    query string with no ownership verification at all, on top of every
    method call here targeting a manager method that either didn't exist
    or had a mismatched signature (see collaboration.py's docstrings for
    the specifics fixed alongside this).
    """
    try:
        deal_uuid = UUID(deal_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Deal no encontrado")
    result = await db.execute(select(Deal).where(Deal.id == deal_uuid))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")
    biz_result = await db.execute(
        select(Business).where(Business.id == deal.business_id, Business.user_id == user.id)
    )
    if not biz_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Deal no encontrado")
    return deal


@router.post("/collaboration/comment")
async def add_comment(
    deal_id: str = Query(...),
    content: str = Body(...),
    mentions: list[str] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add comment to deal."""
    await _verify_deal_access(deal_id, current_user, db)
    comment = await collab_manager.add_comment(
        db, deal_id, str(current_user.id), current_user.full_name, content, mentions
    )

    return {
        "status": "created",
        "comment_id": comment.id,
        "deal_id": deal_id,
        "user_id": comment.user_id,
        "content": content,
        "created_at": comment.created_at.isoformat(),
    }


@router.get("/collaboration/comments/{deal_id}")
async def get_comments(
    deal_id: str,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all comments for deal."""
    await _verify_deal_access(deal_id, current_user, db)
    comments = await collab_manager.get_deal_comments(db, deal_id, limit)

    return {
        "deal_id": deal_id,
        "total": len(comments),
        "comments": [
            {
                "id": c.id,
                "user_id": c.user_id,
                "content": c.content,
                "mentions": c.mentions.split(",") if c.mentions else [],
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ],
    }


@router.post("/collaboration/share")
async def share_deal(
    deal_id: str = Query(...),
    shared_with: str = Query(...),
    permissions: str = Query("read"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Share deal with team member."""
    await _verify_deal_access(deal_id, current_user, db)
    share = await collab_manager.share_deal(db, deal_id, str(current_user.id), shared_with, permissions)

    return {
        "status": "shared",
        "deal_id": deal_id,
        "shared_with": shared_with,
        "permissions": permissions,
        "shared_at": share.shared_at.isoformat(),
    }


@router.post("/collaboration/approval")
async def create_approval(
    action_id: str = Query(...),
    action_type: CollaborationActionEnum = Query(...),
    deal_id: str = Query(..., description="Deal this action applies to, for ownership verification"),
    approvers: list[str] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create approval chain for action."""
    await _verify_deal_access(deal_id, current_user, db)
    approval = await collab_manager.request_approval(
        db, action_id, action_type, str(current_user.id), current_user.full_name, approvers
    )

    return {
        "status": "created",
        "approval_id": approval.id,
        "action_id": action_id,
        "approvers": approvers,
        "created_at": approval.created_at.isoformat(),
    }


@router.post("/collaboration/approve")
async def approve_action(
    action_id: str = Query(...),
    decision: str = Query(..., description="approved or rejected"),
    rejection_reason: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve or reject action. Only someone actually listed as an approver
    on this action can decide it -- collab_manager.approve_action raises if
    current_user isn't one of the chain's approvers."""
    try:
        approval = await collab_manager.approve_action(db, action_id, str(current_user.id), decision, rejection_reason)
    except ValueError:
        return {"status": "not_found"}

    return {
        "status": "updated",
        "action_id": action_id,
        "decision": decision,
        "decided_by": str(current_user.id),
        "decided_at": approval.decision_at.isoformat() if approval.decision_at else None,
    }


@router.get("/collaboration/pending/{user_id}")
async def get_pending_approvals(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pending approvals for user."""
    if user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="No puede ver aprobaciones de otro usuario")
    pending = await collab_manager.get_pending_approvals(db, user_id)

    return {
        "user_id": user_id,
        "pending_count": len(pending),
        "approvals": [
            {
                "id": a.id,
                "action_id": a.action_id,
                "action_type": a.action_type,
                "requested_by": a.requester_id,
                "created_at": a.created_at.isoformat(),
            }
            for a in pending
        ],
    }


@router.get("/collaboration/activity/{deal_id}")
async def get_activity_feed(
    deal_id: str,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get activity feed for deal (comments + shares)."""
    await _verify_deal_access(deal_id, current_user, db)
    activity = await collab_manager.get_deal_activity_feed(db, deal_id, limit)

    return {
        "deal_id": deal_id,
        "total": len(activity),
        "activity": [
            {
                "type": a["type"],
                "id": a["id"],
                "user_id": a["user_id"],
                "timestamp": a["timestamp"].isoformat(),
                **({
                    "content": a.get("content"),
                    "mentions": a.get("mentions", [])
                } if a["type"] == "comment" else {
                    "shared_with": a.get("shared_with"),
                }),
            }
            for a in activity
        ],
    }


@router.websocket("/ws/deal/{deal_id}")
async def websocket_deal(websocket: WebSocket, deal_id: str):
    """WebSocket for real-time deal updates (comments, approvals, shares).

    NOT fixed to real auth or real broadcast in this pass -- this always
    was, and still is, a self-contained echo (it only ever sends events
    back to the same connection that sent them, never to other clients
    watching the same deal_id; there's no connection registry to broadcast
    through). Making it a real multi-client broadcast needs a connection
    manager keyed by deal_id, which is a distinct feature to build, not a
    bug in this one file -- documenting the gap rather than building that
    here. WebSocket auth (a query-param token checked before `accept()`,
    since the Depends(get_current_user) HTTP flow doesn't apply to the
    WS handshake the same way) is part of that same follow-up.
    """
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            if data.startswith("comment:"):
                comment_content = data.replace("comment:", "")
                await websocket.send_json({
                    "type": "comment_added",
                    "deal_id": deal_id,
                    "content": comment_content,
                    "timestamp": datetime.now().isoformat(),
                })

            elif data.startswith("approval:"):
                decision = data.replace("approval:", "")
                await websocket.send_json({
                    "type": "approval_updated",
                    "deal_id": deal_id,
                    "decision": decision,
                    "timestamp": datetime.now().isoformat(),
                })

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
