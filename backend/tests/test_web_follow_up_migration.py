import importlib.util
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database.session import engine
from app.models.lead_follow_up_attempt import LeadFollowUpAttempt


MIGRATION = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "a61f8c2d4e90_add_web_follow_up_channel.py"
)


def test_web_channel_is_allowed_by_model_constraint():
    constraint = next(
        item
        for item in LeadFollowUpAttempt.__table__.constraints
        if item.name == "ck_lead_follow_up_attempts_channel"
    )
    sql = str(constraint.sqltext)
    assert all(channel in sql for channel in (
        "MANUAL", "EMAIL", "WHATSAPP", "WEB",
    ))


def test_migration_has_expected_parent_and_only_changes_constraint():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'down_revision: Union[str, Sequence[str], None] = "94d1bf3b18a7"' in source
    assert "create_check_constraint" in source
    assert "drop_constraint" in source
    assert "create_table" not in source
    assert "add_column" not in source


def test_web_channel_migration_upgrade_and_downgrade_on_postgresql():
    spec = importlib.util.spec_from_file_location("web_channel_migration", MIGRATION)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "a61f8c2d4e90"
    assert migration.down_revision == "94d1bf3b18a7"
    schema = f"test_web_channel_{uuid4().hex}"

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            connection.execute(text("""
                CREATE TABLE lead_follow_up_attempts (
                    id SERIAL PRIMARY KEY,
                    channel VARCHAR(20) NOT NULL,
                    CONSTRAINT ck_lead_follow_up_attempts_channel
                    CHECK (channel IN ('MANUAL', 'EMAIL', 'WHATSAPP'))
                )
            """))
            migration.op = Operations(MigrationContext.configure(connection))
            migration.upgrade()

            for channel in ("MANUAL", "EMAIL", "WHATSAPP", "WEB"):
                connection.execute(
                    text("INSERT INTO lead_follow_up_attempts (channel) VALUES (:channel)"),
                    {"channel": channel},
                )
            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    connection.execute(
                        text("INSERT INTO lead_follow_up_attempts (channel) VALUES ('INVALID')")
                    )

            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    migration.downgrade()

            connection.execute(text(
                "DELETE FROM lead_follow_up_attempts WHERE channel = 'WEB'"
            ))
            migration.downgrade()
            for channel in ("MANUAL", "EMAIL", "WHATSAPP"):
                connection.execute(
                    text("INSERT INTO lead_follow_up_attempts (channel) VALUES (:channel)"),
                    {"channel": channel},
                )
            with pytest.raises(IntegrityError):
                with connection.begin_nested():
                    connection.execute(
                        text("INSERT INTO lead_follow_up_attempts (channel) VALUES ('WEB')")
                    )
        finally:
            transaction.rollback()
