"""Sales Automation service."""
from uuid import UUID
from sqlalchemy.orm import Session

class SalesAutomationService:
    @staticmethod
    def create_email_sequence(business_id: UUID, name: str, emails: list, db: Session = None) -> dict:
        return {"sequence_id": "seq_001", "status": "active"}

    @staticmethod
    def send_sequence(business_id: UUID, sequence_id: str, lead_id: UUID, db: Session = None) -> dict:
        return {"sequence_id": sequence_id, "status": "sent"}

    @staticmethod
    def log_call_followup(business_id: UUID, lead_id: UUID, transcript: str, db: Session = None) -> dict:
        return {"followup_id": "fu_001", "action": "send_proposal"}
