from fastapi import APIRouter, Query, Body, WebSocket
from datetime import datetime
from app.domains.enterprise.collaboration import CollaborationManager

router = APIRouter(tags=["collaboration"])
collab_manager = CollaborationManager()


@router.post("/collaboration/comment")
async def add_comment(
    user_id: str = Query(...),
    deal_id: str = Query(...),
    content: str = Body(...),
    mentions: list[str] = Body(None),
):
    """Add comment to deal."""
    comment = collab_manager.add_comment(deal_id, user_id, content, mentions)

    return {
        "status": "created",
        "comment_id": comment.id,
        "deal_id": deal_id,
        "user_id": user_id,
        "content": content,
        "created_at": comment.created_at.isoformat(),
    }


@router.get("/collaboration/comments/{deal_id}")
async def get_comments(deal_id: str, limit: int = Query(50, le=100)):
    """Get all comments for deal."""
    comments = collab_manager.get_deal_comments(deal_id, limit)

    return {
        "deal_id": deal_id,
        "total": len(comments),
        "comments": [
            {
                "id": c.id,
                "user_id": c.user_id,
                "content": c.content,
                "mentions": c.mentions,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ],
    }


@router.post("/collaboration/share")
async def share_deal(
    user_id: str = Query(...),
    deal_id: str = Query(...),
    shared_with: str = Query(...),
    permissions: str = Query("read"),
):
    """Share deal with team member."""
    share = collab_manager.share_deal(deal_id, user_id, shared_with, permissions)

    return {
        "status": "shared",
        "deal_id": deal_id,
        "shared_with": shared_with,
        "permissions": permissions,
        "shared_at": share.shared_at.isoformat(),
    }


@router.post("/collaboration/approval")
async def create_approval(
    user_id: str = Query(...),
    action_id: str = Query(...),
    action_type: str = Query(...),
    approvers: list[str] = Body(...),
):
    """Create approval chain for action."""
    approval = collab_manager.create_approval_chain(
        action_id, action_type, user_id, approvers
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
    user_id: str = Query(...),
    action_id: str = Query(...),
    decision: str = Query(..., description="approved or rejected"),
):
    """Approve or reject action."""
    approval = collab_manager.approve(action_id, user_id, decision)

    if not approval:
        return {"status": "not_found"}

    return {
        "status": "updated",
        "action_id": action_id,
        "decision": decision,
        "decided_by": user_id,
        "decided_at": approval.decision_at.isoformat() if approval.decision_at else None,
    }


@router.get("/collaboration/pending/{user_id}")
async def get_pending_approvals(user_id: str):
    """Get pending approvals for user."""
    pending = collab_manager.get_pending_approvals(user_id)

    return {
        "user_id": user_id,
        "pending_count": len(pending),
        "approvals": [
            {
                "id": a.id,
                "action_id": a.action_id,
                "action_type": a.action_type,
                "requested_by": a.requested_by,
                "created_at": a.created_at.isoformat(),
            }
            for a in pending
        ],
    }


@router.get("/collaboration/activity/{deal_id}")
async def get_activity_feed(deal_id: str, limit: int = Query(50, le=100)):
    """Get activity feed for deal (comments + shares)."""
    activity = collab_manager.get_deal_activity_feed(deal_id, limit)

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
    """WebSocket for real-time deal updates (comments, approvals, shares)."""
    await websocket.accept()

    % Simulate real-time events %
    try:
        while True:
            data = await websocket.receive_text()

            if data.startswith("comment:"):
                % Broadcast comment to all clients on this deal %
                comment_content = data.replace("comment:", "")
                await websocket.send_json({
                    "type": "comment_added",
                    "deal_id": deal_id,
                    "content": comment_content,
                    "timestamp": datetime.now().isoformat(),
                })

            elif data.startswith("approval:"):
                % Broadcast approval update %
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
