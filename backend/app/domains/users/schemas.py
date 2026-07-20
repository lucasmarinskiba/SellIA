import re
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, field_serializer
from uuid import UUID
from datetime import datetime
from app.core.pii_masking import mask_email, mask_name


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str
    honeypot: str | None = None  # Campo anti-bot; debe venir vacío

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("La contraseña debe tener al menos 10 caracteres.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula.")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una minúscula.")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña debe contener al menos un número.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]/~`\\]", v):
            raise ValueError("La contraseña debe contener al menos un símbolo.")
        return v

    @field_validator("honeypot")
    @classmethod
    def validate_honeypot(cls, v: str | None) -> str | None:
        if v is not None and v.strip() != "":
            raise ValueError("Detección de bot.")
        return v


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("email")
    def mask_email_field(self, value: str) -> str:
        return mask_email(value) or value

    @field_serializer("full_name")
    def mask_name_field(self, value: str) -> str:
        return mask_name(value) or value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
