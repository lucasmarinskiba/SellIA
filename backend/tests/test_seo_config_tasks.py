"""The seo_config Celery tasks must run, twice in a row, against the real schema.

Seen in production: most seo_config tables did not exist (their model modules are not named
``models.py`` so the bootstrap never registered them, and ``publication_links`` was blocked on a
foreign key to ``products``), ``monitor_fomo_decay`` filtered on ``Business.active`` (the column is
``is_active``), and the module still used ``asyncio.run`` instead of the shared event-loop bridge.
"""

from __future__ import annotations

import pytest

SEO_TASKS = [
    "fetch_nightly_analytics",
    "generate_fomo_cadence",
    "compute_analytics_summaries",
    "check_ab_test_winners",
    "monitor_fomo_decay",
    "compute_positioning_scores",
    "compute_store_positioning_scores",
]

#: Tables the tasks above read or write, from model modules the bootstrap scan does not find.
TABLES_THE_TASKS_NEED = {
    "publication_link_metrics",
    "publication_link_perf_summary",
    "conversion_events",
    "seo_fomo_ab_tests",
    "fomo_decay_logs",
    "publication_link_positioning_scores",
    "positioning_recommendations",
}


def test_the_bootstrap_registers_every_table_the_seo_tasks_need() -> None:
    from app.core.database import Base
    from app.db.schema_bootstrap import _import_all_models

    _import_all_models()
    assert TABLES_THE_TASKS_NEED <= set(Base.metadata.tables)


def test_the_decay_monitor_filters_on_a_column_that_exists() -> None:
    from app.domains.businesses.models import Business

    assert hasattr(Business, "is_active") and not hasattr(Business, "active")
    from pathlib import Path

    import app.domains.seo_config.tasks as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "Business.active" not in source


@pytest.mark.parametrize("name", SEO_TASKS)
async def test_each_task_runs_twice_in_a_row(db_session, name: str) -> None:
    """Twice, because the original failure only showed from the second run on."""
    import asyncio

    from app.domains.seo_config import tasks

    task = getattr(tasks, name)
    for _ in range(2):
        # A worker thread has no running loop, like a Celery process; run_async refuses to be
        # called from inside one. Raises if a table or column is missing.
        await asyncio.to_thread(task.run)


def test_seo_config_index_names_are_not_shared_with_other_tables() -> None:
    """Index names are unique per PostgreSQL schema: a name reused by another table makes the
    second CREATE INDEX fail with DuplicateTable and that table is silently never created
    (publication_link_metrics lost to attribution_metrics' "idx_business_metrics")."""
    from collections import defaultdict

    from app.core.database import Base
    from app.db.schema_bootstrap import _import_all_models

    _import_all_models()
    owners: dict[str, set[str]] = defaultdict(set)
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            if index.name:
                owners[index.name].add(table.name)

    seo_tables = {
        "publication_link_metrics", "publication_link_perf_summary", "conversion_events", "seo_fomo_ab_tests",
        "fomo_decay_logs", "publication_link_positioning_scores", "positioning_recommendations",
    }
    shared = {name: sorted(tables) for name, tables in owners.items() if len(tables) > 1 and tables & seo_tables}
    assert not shared, f"index names shared with other tables: {shared}"
