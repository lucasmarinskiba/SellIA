"""Voice Agent API Router"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.voice.models import VoiceCall, VoiceConfig
from app.domains.voice.schemas import (
    VoiceCallCreate,
    VoiceCallResponse,
    VoiceCallUpdate,
    VoiceConfigResponse,
    VoiceConfigCreate,
    VoiceConfigUpdate,
    SpeechRequest,
    TranscriptionResponse,
    CallSegmentResponse,
)
from app.domains.voice.service import VoiceService

router = APIRouter(prefix="/voice", tags=["voice"])


# ========== Calls ==========

@router.post("/calls", response_model=VoiceCallResponse, status_code=status.HTTP_201_CREATED)
async def create_call(
    data: VoiceCallCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VoiceService(db)
    call = await service.create_call(
        business_id=data.business_id,
        customer_id=data.customer_id,
        phone_number=data.phone_number,
        direction=data.direction,
    )
    return call


@router.get("/calls", response_model=list[VoiceCallResponse])
async def list_calls(
    business_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(VoiceCall).where(VoiceCall.business_id == business_id)
    if status:
        query = query.where(VoiceCall.status == status)
    query = query.order_by(desc(VoiceCall.created_at))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/calls/{call_id}", response_model=VoiceCallResponse)
async def get_call(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(VoiceCall).where(VoiceCall.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return call


@router.post("/calls/{call_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_call_audio(
    call_id: UUID,
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VoiceService(db)
    result = await db.execute(select(VoiceCall).where(VoiceCall.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")

    audio_bytes = await audio.read()
    transcript = await service.transcribe_audio(
        audio_bytes,
        provider=call.extra_data.get("stt_provider", "openai_whisper"),
    )
    return TranscriptionResponse(transcript=transcript)


@router.post("/calls/{call_id}/speak")
async def generate_call_speech(
    call_id: UUID,
    req: SpeechRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VoiceService(db)
    result = await db.execute(select(VoiceCall).where(VoiceCall.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")

    voice_config = await service._get_voice_config(call.business_id)
    audio_bytes = await service.generate_speech(req.text, voice_config)
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/calls/{call_id}/process-segment", response_model=CallSegmentResponse)
async def process_call_segment(
    call_id: UUID,
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VoiceService(db)
    audio_bytes = await audio.read()
    try:
        segment = await service.process_call_segment(call_id, audio_bytes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return CallSegmentResponse(**segment)


@router.patch("/calls/{call_id}", response_model=VoiceCallResponse)
async def update_call(
    call_id: UUID,
    data: VoiceCallUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(VoiceCall).where(VoiceCall.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(call, field, value)
    await db.commit()
    await db.refresh(call)
    return call


@router.post("/calls/{call_id}/end", response_model=VoiceCallResponse)
async def end_call(
    call_id: UUID,
    outcome: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VoiceService(db)
    try:
        call = await service.end_call(call_id, outcome)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return call


# ========== Config ==========

@router.get("/config", response_model=VoiceConfigResponse)
async def get_voice_config(
    business_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(VoiceConfig).where(VoiceConfig.business_id == business_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de voz no encontrada")
    return config


@router.post("/config", response_model=VoiceConfigResponse, status_code=status.HTTP_201_CREATED)
async def upsert_voice_config(
    data: VoiceConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VoiceService(db)
    config = await service.upsert_config(data.model_dump())
    return config


@router.patch("/config/{config_id}", response_model=VoiceConfigResponse)
async def update_voice_config(
    config_id: UUID,
    data: VoiceConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(VoiceConfig).where(VoiceConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de voz no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    from datetime import datetime, timezone
    config.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(config)
    return config


# ========== Webhooks ==========

@router.post("/webhook/twilio")
async def twilio_webhook(
    db: AsyncSession = Depends(get_db),
):
    """Twilio webhook placeholder — implement call status & media URL handling."""
    return {"status": "received", "provider": "twilio"}
