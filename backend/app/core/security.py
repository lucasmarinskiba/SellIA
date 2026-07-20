import re
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from app.core.config import get_settings

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def validate_password_strength(password: str) -> None:
    """Valida que la contraseña cumpla con los requisitos de seguridad.
    Lanza ValueError con mensaje descriptivo si no cumple.
    """
    if len(password) < 10:
        raise ValueError("La contraseña debe tener al menos 10 caracteres.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una minúscula.")
    if not re.search(r"[0-9]", password):
        raise ValueError("La contraseña debe contener al menos un número.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]/~`\\]", password):
        raise ValueError("La contraseña debe contener al menos un símbolo.")


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
