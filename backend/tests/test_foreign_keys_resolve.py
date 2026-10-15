"""Every ForeignKey of a registered model must point at a table that exists.

Ten tables (channel_affinity_models, message_routings, channel_routing_models, churn_prediction_models,
clv_models, lead_scoring_models, location_message_executions, offline_to_online_attribution,
post_visit_sequence_executions, proximity_events) declared ``ForeignKey("customers.id")``, but no
model declares a ``customers`` table, so they could never be created: SQLAlchemy raised
NoReferencedTableError and the schema bootstrap skipped them on every boot. The services that write
them receive the user/customer id from the caller (a free-form UUID), so the column stays a plain
indexed UUID instead of a constraint that can never exist.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import NoReferencedTableError

TABLES_THAT_REFERENCED_CUSTOMERS = [
    "channel_affinity_models",
    "message_routings",
    "channel_routing_models",
    "churn_prediction_models",
    "clv_models",
    "lead_scoring_models",
    "location_message_executions",
    "offline_to_online_attribution",
    "post_visit_sequence_executions",
    "proximity_events",
]


def _registered_metadata():
    import app.main  # noqa: F401  -- load every router and model, like the web process
    from app.core.database import Base
    from app.db.schema_bootstrap import _import_all_models

    _import_all_models()
    return Base.metadata


def test_no_model_references_a_customers_table() -> None:
    metadata = _registered_metadata()
    offenders = sorted(
        f"{table.name}.{fk.parent.name}"
        for table in metadata.tables.values()
        for fk in table.foreign_keys
        if fk._colspec.split(".")[0] == "customers"
    )
    assert not offenders, offenders


def test_every_foreign_key_of_a_registered_table_resolves() -> None:
    metadata = _registered_metadata()
    unresolved = []
    for table in metadata.tables.values():
        for fk in table.foreign_keys:
            try:
                _ = fk.column
            except NoReferencedTableError:
                unresolved.append(f"{table.name}.{fk.parent.name} -> {fk._colspec}")
    assert not unresolved, unresolved


@pytest.mark.parametrize("table", TABLES_THAT_REFERENCED_CUSTOMERS)
async def test_the_table_is_created_by_the_bootstrap(db_session, table: str) -> None:
    """The test database is built with ensure_all_tables (see conftest)."""
    exists = (await db_session.execute(text("SELECT to_regclass(:name)"), {"name": table})).scalar_one()
    assert exists is not None


async def test_an_id_that_is_not_a_user_can_be_stored(db_session, test_user) -> None:
    """The reason for dropping the constraint: callers pass ids of leads/contacts, not only users."""
    import uuid

    from sqlalchemy import select

    from app.domains.businesses.models import Business
    from app.domains.ml_pipelines.models import ChurnPredictionModel

    business = Business(user_id=test_user.id, name=f"FK {uuid.uuid4().hex[:6]}")
    db_session.add(business)
    await db_session.commit()
    business_id = business.id
    customer_id = uuid.uuid4()  # not a row of any table

    db_session.add(ChurnPredictionModel(business_id=business_id, customer_id=customer_id, churn_probability=0.4))
    await db_session.commit()
    try:
        stored = (
            await db_session.execute(
                select(ChurnPredictionModel.customer_id).where(ChurnPredictionModel.business_id == business_id)
            )
        ).scalar_one()
        assert stored == customer_id
    finally:
        await db_session.execute(ChurnPredictionModel.__table__.delete().where(ChurnPredictionModel.business_id == business_id))
        await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
        await db_session.commit()
