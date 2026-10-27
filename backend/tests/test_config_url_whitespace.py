"""Settings: URL values lose stray whitespace/CR-LF; secrets are left exactly as given."""

import os

os.environ.setdefault("ENVIRONMENT", "testing")

from app.core.config import Settings

BASE = dict(DATABASE_URL="postgresql+asyncpg://tester@localhost/testdb", SECRET_KEY="k" * 40)


def test_a_carriage_return_on_frontend_url_does_not_reach_redirects():
    s = Settings(**BASE, FRONTEND_URL="https://sellia-brain.vercel.app\r")
    assert s.FRONTEND_URL == "https://sellia-brain.vercel.app"
    redirect = f"{s.FRONTEND_URL}/dashboard/canales?connect_error=state"
    assert "\r" not in redirect and "\n" not in redirect


def test_redirect_uris_are_trimmed_too():
    s = Settings(**BASE, META_REDIRECT_URI="  https://x.app/cb\r\n", MERCADO_LIBRE_REDIRECT_URI="https://x.app/ml\n")
    assert s.META_REDIRECT_URI == "https://x.app/cb"
    assert s.MERCADO_LIBRE_REDIRECT_URI == "https://x.app/ml"


def test_secrets_are_not_modified():
    key = "k" * 40 + "\r"
    assert Settings(DATABASE_URL=BASE["DATABASE_URL"], SECRET_KEY=key).SECRET_KEY == key
