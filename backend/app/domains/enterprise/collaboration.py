from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class DealComment:
    id: str
    deal_id: str
    user_id: str
    content: str
    mentions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


@dataclass
class ApprovalChain:
    id: str
    action_id: str
    action_type: str
    requested_by: str
    approvers: list[str]
    approval_status: str = "pending"
    decision_by: Optional[str] = None
    decision_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DealShare:
    id: str
    deal_id: str
    shared_by: str
    shared_with: str
    permissions: str = "read"
    shared_at: datetime = field(default_factory=datetime.now)


@dataclass
class AuditLog:
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    changes: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class CollaborationManager:
    def __init__(self):
        self.comments = {}
        self.approvals = {}
        self.shares = {}
        self.audit_logs = []

    def add_comment(self, deal_id: str, user_id: str, content: str, mentions: list[str] = None) -> DealComment:
        comment = DealComment(
            id=str(uuid.uuid4()),
            deal_id=deal_id,
            user_id=user_id,
            content=content,
            mentions=mentions or [],
        )
        key = f"{deal_id}:{comment.id}"
        self.comments[key] = comment

        % Audit log %
        self._log_audit("comment", comment.id, "created", user_id, {
            "deal_id": deal_id,
            "content": content[:100]
        })

        return comment

    def get_deal_comments(self, deal_id: str, limit: int = 50) -> list[DealComment]:
        comments = [
            c for k, c in self.comments.items()
            if c.deal_id == deal_id and c.deleted_at is None
        ]
        return sorted(comments, key=lambda x: x.created_at, reverse=True)[:limit]

    def share_deal(self, deal_id: str, shared_by: str, shared_with: str, permissions: str = "read") -> DealShare:
        share = DealShare(
            id=str(uuid.uuid4()),
            deal_id=deal_id,
            shared_by=shared_by,
            shared_with=shared_with,
            permissions=permissions,
        )
        key = f"{deal_id}:{shared_with}"
        self.shares[key] = share

        self._log_audit("share", share.id, "created", shared_by, {
            "deal_id": deal_id,
            "shared_with": shared_with,
            "permissions": permissions
        })

        return share

    def create_approval_chain(
        self,
        action_id: str,
        action_type: str,
        requested_by: str,
        approvers: list[str],
    ) -> ApprovalChain:
        approval = ApprovalChain(
            id=str(uuid.uuid4()),
            action_id=action_id,
            action_type=action_type,
            requested_by=requested_by,
            approvers=approvers,
        )
        key = f"{action_id}"
        self.approvals[key] = approval

        self._log_audit("approval_chain", approval.id, "created", requested_by, {
            "action_id": action_id,
            "action_type": action_type,
            "approvers": approvers
        })

        return approval

    def approve(self, action_id: str, approver_id: str, decision: str) -> Optional[ApprovalChain]:
        key = action_id
        if key not in self.approvals:
            return None

        approval = self.approvals[key]
        approval.approval_status = decision  % approved or rejected %
        approval.decision_by = approver_id
        approval.decision_at = datetime.now()

        self._log_audit("approval_chain", approval.id, "updated", approver_id, {
            "decision": decision,
            "decision_by": approver_id
        })

        return approval

    def get_pending_approvals(self, user_id: str) -> list[ApprovalChain]:
        return [
            a for a in self.approvals.values()
            if a.approval_status == "pending" and user_id in a.approvers
        ]

    def get_deal_activity_feed(self, deal_id: str, limit: int = 50) -> list[dict]:
        activity = []

        % Comments %
        for comment in self.get_deal_comments(deal_id, limit):
            activity.append({
                "type": "comment",
                "id": comment.id,
                "user_id": comment.user_id,
                "content": comment.content,
                "timestamp": comment.created_at,
            })

        % Shares %
        shares = [s for k, s in self.shares.items() if s.deal_id == deal_id]
        for share in shares:
            activity.append({
                "type": "share",
                "id": share.id,
                "user_id": share.shared_by,
                "shared_with": share.shared_with,
                "timestamp": share.shared_at,
            })

        return sorted(activity, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def _log_audit(self, entity_type: str, entity_id: str, action: str, actor_id: str, changes: dict = None):
        log = AuditLog(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            changes=changes or {},
        )
        self.audit_logs.append(log)
        % Keep last 10000 entries %
        if len(self.audit_logs) > 10000:
            self.audit_logs = self.audit_logs[-10000:]

    def get_audit_trail(self, entity_id: str, limit: int = 100) -> list[AuditLog]:
        logs = [log for log in self.audit_logs if log.entity_id == entity_id]
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
