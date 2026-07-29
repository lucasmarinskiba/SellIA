"""
Email Automation Workflows
- Secuencias automáticas: 5-email cold sequences, nurture flows
- Triggers: time-based, status-based, engagement-based
- Templating + personalization
- Scheduling + delivery tracking
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

# ============================================================
# ENUMS
# ============================================================
class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class TriggerType(str, Enum):
    TIME_DELAY = "time_delay"  # Enviar X días después de evento
    STATUS_CHANGE = "status_change"  # Cuando lead cambia status
    NO_ENGAGEMENT = "no_engagement"  # Si no abre/clickea en X días
    MANUAL = "manual"  # Trigger manual

class EmailStatus(str, Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"

# ============================================================
# MODELOS
# ============================================================
class EmailTemplate(BaseModel):
    subject: str
    body: str
    # Variables: {lead_name}, {company}, {offer}, {button_url}
    cta_text: str = "Learn More"
    cta_url: Optional[str] = None

class WorkflowStep(BaseModel):
    step_number: int
    trigger_type: TriggerType
    delay_days: Optional[int] = None  # Si TIME_DELAY
    trigger_status: Optional[str] = None  # Si STATUS_CHANGE
    email_template: EmailTemplate
    enabled: bool = True

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    industry_filter: Optional[str] = None  # "SaaS", "Tech", etc. o None para all
    min_score_filter: float = 0  # Solo aplicar a leads con score >= X
    steps: List[WorkflowStep]

class Workflow(WorkflowBase):
    id: int
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime
    active_leads: int  # Cuántos leads en este workflow

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    steps: Optional[List[WorkflowStep]] = None

class WorkflowExecution(BaseModel):
    id: int
    workflow_id: int
    lead_id: int
    lead_email: str
    step_number: int
    email_status: EmailStatus
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    bounce_reason: Optional[str]

# ============================================================
# IN-MEMORY STORAGE
# ============================================================
workflows_db = {}
workflow_executions_db = {}
next_workflow_id = 1
next_execution_id = 1

# Predefined workflows
PREDEFINED_WORKFLOWS = {
    "cold_outreach_saas": {
        "name": "Cold Outreach - SaaS",
        "description": "5-email cold sequence for SaaS prospects",
        "industry_filter": "SaaS",
        "min_score_filter": 50,
        "steps": [
            {
                "step_number": 1,
                "trigger_type": TriggerType.MANUAL,
                "email_template": {
                    "subject": "Quick question about {company}",
                    "body": """Hi {lead_name},

Noticed {company} is in the {industry} space. We work with similar companies to streamline their sales process.

Would you be open to a 15-min conversation?

{cta_text}
{button_url}

Best,
SellIA Team""",
                    "cta_text": "Book a time",
                    "cta_url": "https://calendly.com/sellia"
                }
            },
            {
                "step_number": 2,
                "trigger_type": TriggerType.TIME_DELAY,
                "delay_days": 3,
                "email_template": {
                    "subject": "Re: Quick question about {company}",
                    "body": """Hi {lead_name},

Following up on my earlier message. Most SaaS teams see 40% faster close rates with automated workflows.

Do you want to see how?

{cta_text}
{button_url}

Best,
SellIA Team""",
                    "cta_text": "Show me",
                    "cta_url": "https://calendly.com/sellia"
                }
            },
            {
                "step_number": 3,
                "trigger_type": TriggerType.TIME_DELAY,
                "delay_days": 5,
                "email_template": {
                    "subject": "Social proof from {industry} companies",
                    "body": """Hi {lead_name},

Top SaaS companies like Stripe, Calendly, and Notion use automation to scale sales.

See the playbook:

{cta_text}
{button_url}

Best,
SellIA Team""",
                    "cta_text": "View playbook",
                    "cta_url": "https://example.com/playbook"
                }
            },
            {
                "step_number": 4,
                "trigger_type": TriggerType.NO_ENGAGEMENT,
                "delay_days": 7,
                "email_template": {
                    "subject": "Last message: ROI calculator for {company}",
                    "body": """Hi {lead_name},

Since you haven't opened my previous messages, I'm guessing you're busy.

Here's a quick ROI calculator so you can see savings in 2 minutes:

{cta_text}
{button_url}

If not interested, just let me know.

Best,
SellIA Team""",
                    "cta_text": "Calculate ROI",
                    "cta_url": "https://example.com/roi"
                }
            }
        ]
    },
    "nurture_engaged": {
        "name": "Nurture Engaged Leads",
        "description": "Weekly value emails for leads who engaged",
        "industry_filter": None,
        "min_score_filter": 60,
        "steps": [
            {
                "step_number": 1,
                "trigger_type": TriggerType.STATUS_CHANGE,
                "trigger_status": "contacted",
                "email_template": {
                    "subject": "3 sales trends in {industry}",
                    "body": """Hi {lead_name},

Glad we connected. Here are 3 trends shaping {industry} right now:

1. AI-driven automation (30% faster deals)
2. Buyer enablement (50% higher close rates)
3. Predictive analytics (better lead scoring)

Which one is most relevant to {company}?

Best,
SellIA Team"""
                }
            },
            {
                "step_number": 2,
                "trigger_type": TriggerType.TIME_DELAY,
                "delay_days": 7,
                "email_template": {
                    "subject": "How {company} can implement AI-driven selling",
                    "body": """Hi {lead_name},

Following up on AI-driven automation. Here's a 3-step framework:

1. Score leads (fit + engagement)
2. Prioritize top 20% (Pareto)
3. Auto-sequence (personalized at scale)

Want to see this in action?

{cta_text}
{button_url}

Best,
SellIA Team""",
                    "cta_text": "See demo",
                    "cta_url": "https://calendly.com/sellia/demo"
                }
            }
        ]
    }
}

# ============================================================
# FUNCIONES
# ============================================================
def render_email_template(template: EmailTemplate, lead_data: dict) -> tuple:
    """Renderizar template con datos del lead."""
    subject = template.subject
    body = template.body
    cta_url = template.cta_url or ""

    # Variables para reemplazar
    replacements = {
        "{lead_name}": lead_data.get("name", "there"),
        "{company}": lead_data.get("company", "your company"),
        "{industry}": lead_data.get("industry", "your industry"),
        "{offer}": lead_data.get("offer", "SellIA"),
        "{button_url}": f"[{template.cta_text}]({cta_url})",
        "{cta_text}": f"[{template.cta_text}]({cta_url})",
    }

    for key, value in replacements.items():
        subject = subject.replace(key, value)
        body = body.replace(key, value)

    return subject, body

# ============================================================
# ENDPOINTS
# ============================================================
@router.post("/", response_model=Workflow)
async def create_workflow(workflow_data: WorkflowCreate) -> dict:
    """Crear workflow automático."""
    global next_workflow_id

    workflow_dict = workflow_data.dict()
    workflow_dict['id'] = next_workflow_id
    workflow_dict['status'] = WorkflowStatus.DRAFT
    workflow_dict['created_at'] = datetime.now()
    workflow_dict['updated_at'] = datetime.now()
    workflow_dict['active_leads'] = 0

    workflows_db[next_workflow_id] = workflow_dict
    logger.info(f"Workflow creado: {workflow_dict['name']} (id: {next_workflow_id})")
    next_workflow_id += 1

    return workflow_dict

@router.get("/", response_model=List[Workflow])
async def list_workflows(status: Optional[WorkflowStatus] = None) -> list:
    """Listar workflows."""
    workflows_list = list(workflows_db.values())

    if status:
        workflows_list = [w for w in workflows_list if w['status'] == status]

    return workflows_list

@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: int) -> dict:
    """Obtener detalles workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    return workflows_db[workflow_id]

@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: int, workflow_update: WorkflowUpdate) -> dict:
    """Actualizar workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    workflow = workflows_db[workflow_id]
    update_data = workflow_update.dict(exclude_unset=True)

    workflow.update(update_data)
    workflow['updated_at'] = datetime.now()

    logger.info(f"Workflow actualizado: {workflow_id}")
    return workflow

@router.post("/{workflow_id}/activate")
async def activate_workflow(workflow_id: int) -> dict:
    """Activar workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    workflow = workflows_db[workflow_id]
    workflow['status'] = WorkflowStatus.ACTIVE
    workflow['updated_at'] = datetime.now()

    logger.info(f"Workflow activado: {workflow_id}")
    return workflow

@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: int) -> dict:
    """Pausar workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    workflow = workflows_db[workflow_id]
    workflow['status'] = WorkflowStatus.PAUSED
    workflow['updated_at'] = datetime.now()

    logger.info(f"Workflow pausado: {workflow_id}")
    return workflow

@router.post("/template/preview")
async def preview_email(workflow_id: int, lead_id: int) -> dict:
    """Preview de email con datos reales del lead."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    workflow = workflows_db[workflow_id]

    # Simular datos del lead (en prod, traer de lead DB)
    lead_data = {
        "name": "John Doe",
        "company": "Acme Corp",
        "industry": "SaaS",
        "offer": "SellIA Platform"
    }

    step = workflow['steps'][0]
    subject, body = render_email_template(step['email_template'], lead_data)

    return {
        "workflow_id": workflow_id,
        "step": step['step_number'],
        "subject": subject,
        "body": body,
        "cta": step['email_template']['cta_text']
    }

@router.post("/{workflow_id}/enroll-lead")
async def enroll_lead_in_workflow(workflow_id: int, lead_id: int) -> dict:
    """Enrollar lead en workflow automático."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")

    workflow = workflows_db[workflow_id]

    # Crear ejecución para el primer paso
    global next_execution_id

    execution_dict = {
        'id': next_execution_id,
        'workflow_id': workflow_id,
        'lead_id': lead_id,
        'lead_email': f"lead{lead_id}@example.com",  # En prod, traer de lead DB
        'step_number': 1,
        'email_status': EmailStatus.SCHEDULED,
        'sent_at': None,
        'opened_at': None,
        'clicked_at': None,
        'bounce_reason': None
    }

    workflow_executions_db[next_execution_id] = execution_dict
    workflow['active_leads'] += 1

    logger.info(f"Lead {lead_id} enrolled en workflow {workflow_id}")
    next_execution_id += 1

    return execution_dict

@router.get("/executions/list")
async def list_executions(
    workflow_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    status: Optional[EmailStatus] = None
) -> List[WorkflowExecution]:
    """Listar ejecuciones de emails."""
    executions = list(workflow_executions_db.values())

    if workflow_id:
        executions = [e for e in executions if e['workflow_id'] == workflow_id]
    if lead_id:
        executions = [e for e in executions if e['lead_id'] == lead_id]
    if status:
        executions = [e for e in executions if e['email_status'] == status]

    return executions

@router.post("/templates/predefined/{template_name}")
async def create_from_predefined(template_name: str) -> dict:
    """Crear workflow desde template predefinido."""
    if template_name not in PREDEFINED_WORKFLOWS:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    template = PREDEFINED_WORKFLOWS[template_name]
    workflow_data = WorkflowCreate(**template)

    return await create_workflow(workflow_data)

@router.get("/templates/predefined")
async def list_predefined_templates() -> dict:
    """Listar templates predefinidos."""
    return {
        name: {
            "name": data["name"],
            "description": data["description"],
            "steps": len(data["steps"])
        }
        for name, data in PREDEFINED_WORKFLOWS.items()
    }
