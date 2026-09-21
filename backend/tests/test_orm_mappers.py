"""Whole-app ORM sanity check.

A table-name collision between two models (same MetaData) or an unresolved
relationship target does not fail at import time of the offending module: it
makes SQLAlchemy's mapper configuration fail the first time *any* model is used,
app-wide, and silently drops routers ("Skipped extra router ...") in production.
Checking a single module or router import does not catch it, so configure every
mapper once, exactly as the first real query would.

History: `seo_config.fomo_models.FOMABTest` reused `fomo_ab_tests` (owned by
`domains/fomo`), and `models/email_auth.EmailTemplate` reused `email_templates`
(owned by `domains/automations`). Both shipped to main unnoticed.
"""

from sqlalchemy.orm import configure_mappers


def test_all_mappers_configure() -> None:
    import app.main  # noqa: F401 -- importing the app registers every mounted model

    configure_mappers()
