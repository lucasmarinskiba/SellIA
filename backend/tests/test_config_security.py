"""Tests de seguridad de configuración — fija el fail-fast de Settings.

`Settings.validate_security` es la primera línea de defensa: aborta el arranque
si los secretos son débiles, por defecto o faltan en producción. Estos tests
bloquean regresiones que reabrirían esos huecos. Sin infraestructura (puro
modelo Pydantic); las kwargs de init tienen prioridad sobre .env / entorno.
"""

import pytest

from app.core.config import Settings

# Secreto válido genérico (≥32 chars, no está en la lista de inseguros).
_GOOD_SECRET = "x7k2p9w4m1n8q3r6t5y0z" + "a" * 20


def _settings(**kw) -> Settings:
    # _env_file=None → ignora el .env del repo para que el test sea determinista.
    return Settings(_env_file=None, **kw)


@pytest.fixture(autouse=True)
def _clear_fernet(monkeypatch):
    # validate_security lee FERNET_SECRET de os.environ directamente.
    monkeypatch.delenv("FERNET_SECRET", raising=False)


# ── SECRET_KEY ──────────────────────────────────────────────────────────────
def test_short_secret_key_rejected():
    with pytest.raises(ValueError, match="32 caracteres"):
        _settings(SECRET_KEY="corta", ENVIRONMENT="development")


def test_insecure_default_secret_rejected():
    with pytest.raises(ValueError, match="por defecto inseguro"):
        _settings(
            SECRET_KEY="supersecretkeychangethisinproduction",
            ENVIRONMENT="development",
        )


def test_missing_secret_in_production_rejected():
    with pytest.raises(ValueError, match="SECRET_KEY es requerido"):
        _settings(SECRET_KEY="", ENVIRONMENT="production", SIDECAR_SHARED_SECRET="s")


def test_dev_assigns_temporary_secret_when_empty():
    # En development sin SECRET_KEY → asigna placeholder (no aborta).
    s = _settings(SECRET_KEY="", ENVIRONMENT="development")
    assert len(s.SECRET_KEY) >= 32


# ── producción: defaults peligrosos ─────────────────────────────────────────
def test_production_default_db_password_rejected():
    with pytest.raises(ValueError, match="devpassword123"):
        _settings(
            SECRET_KEY=_GOOD_SECRET,
            ENVIRONMENT="production",
            SIDECAR_SHARED_SECRET="s",
            DATABASE_URL="postgresql+asyncpg://u:devpassword123@db:5432/x",
        )


def test_production_requires_sidecar_secret():
    with pytest.raises(ValueError, match="SIDECAR_SHARED_SECRET"):
        _settings(
            SECRET_KEY=_GOOD_SECRET,
            ENVIRONMENT="production",
            SIDECAR_SHARED_SECRET="",
            DATABASE_URL="postgresql+asyncpg://u:safe_pwd_here@db:5432/x",
        )


def test_production_ok_with_strong_config():
    s = _settings(
        SECRET_KEY=_GOOD_SECRET,
        ENVIRONMENT="production",
        SIDECAR_SHARED_SECRET="sidecar-secret",
        DATABASE_URL="postgresql+asyncpg://u:safe_pwd_here@db:5432/x",
    )
    assert s.ENVIRONMENT == "production"
    assert s.SECRET_KEY == _GOOD_SECRET


# ── FERNET_SECRET ────────────────────────────────────────────────────────────
def test_short_fernet_secret_rejected(monkeypatch):
    monkeypatch.setenv("FERNET_SECRET", "tooshort")
    with pytest.raises(ValueError, match="FERNET_SECRET"):
        _settings(SECRET_KEY=_GOOD_SECRET, ENVIRONMENT="development")
