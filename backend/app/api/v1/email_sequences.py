"""
Cold email sequence generation + sending.
Uses Efti (cold email) + Kennedy (80/20 ROI) frameworks.
"""
import os
import httpx
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/sequences", tags=["email_sequences"])


class LeadProfile(BaseModel):
    name: str
    email: str
    company: str
    title: str
    pain_point: str
    industry: str


class EmailInSequence(BaseModel):
    day: int
    subject: str
    body: str


class SequenceRequest(BaseModel):
    lead: LeadProfile
    offer: str
    sender_name: str = "SellIA"
    sender_email: str


async def _generate_cold_email_sequence(lead: LeadProfile, offer: str) -> list[EmailInSequence]:
    """Generate 5-email cold sequence using Efti + Kennedy frameworks."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    prompt = f"""Generate a 5-email cold outreach sequence for lead prospecting using the Efti cold email framework + Kennedy 80/20 ROI principles.

LEAD PROFILE:
- Name: {lead.name}
- Company: {lead.company}
- Title: {lead.title}
- Pain Point: {lead.pain_point}
- Industry: {lead.industry}

OFFER: {offer}

EFTI COLD EMAIL FRAMEWORK (Ramit Sethi):
1. Subject line: curiosity + specificity (avoid salesy)
2. Personalization: reference something specific about them/company
3. Value first: show you understand their problem
4. Social proof: brief credibility (results, testimonials)
5. CTA: single, low-friction (call, short meeting, reply)
6. Short: 50-75 words body
7. Respect time: acknowledge you're interrupting

KENNEDY 80/20:
- Focus on highest-value outcome for them
- ROI language (money, time, risk reduction)
- Skip features; lead with results

Generate JSON array with 5 emails:
[
  {"day": 1, "subject": "...", "body": "..."},
  {"day": 3, "subject": "...", "body": "..."},
  ...
]

Each email builds on previous without repeating. Day 1 is introduction, Day 3 adds social proof, Day 5 creates urgency, Day 7 final value angle, Day 10 graceful exit.

Return ONLY valid JSON array, no markdown."""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["content"][0]["text"]
    # Parse JSON from response
    import json
    emails_data = json.loads(content)
    return [EmailInSequence(**e) for e in emails_data]


@router.post("/cold-email")
async def create_cold_email_sequence(req: SequenceRequest) -> dict:
    """Generate cold email sequence for lead."""
    try:
        emails = await _generate_cold_email_sequence(req.lead, req.offer)
        return {
            "sequence_id": f"seq_{datetime.now().timestamp()}",
            "lead": req.lead,
            "emails": emails,
            "status": "generated",
            "created_at": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
