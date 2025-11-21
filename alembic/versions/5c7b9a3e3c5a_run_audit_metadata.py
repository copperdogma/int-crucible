"""Add run audit metadata fields.

Revision ID: 5c7b9a3e3c5a
Revises: b88f38b6830a
Create Date: 2025-11-20 18:13:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "5c7b9a3e3c5a"
down_revision = "b88f38b6830a"
branch_labels = None
depends_on = None


run_trigger_source_enum = sa.Enum(
    "run_config_panel",
    "api_client",
    "integration_test",
    "cli_tool",
    name="runtriggersource",
)


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("crucible_runs")}

    run_trigger_source_enum.create(bind, checkfirst=True)

    def add_column_if_missing(name: str, column: sa.Column) -> None:
        if name not in existing_columns:
            op.add_column("crucible_runs", column)
            existing_columns.add(name)

    add_column_if_missing("recommended_message_id", sa.Column("recommended_message_id", sa.String(), nullable=True))
    add_column_if_missing("recommended_config_snapshot", sa.Column("recommended_config_snapshot", sa.JSON(), nullable=True))
    add_column_if_missing("ui_trigger_id", sa.Column("ui_trigger_id", sa.String(length=64), nullable=True))
    add_column_if_missing("ui_trigger_source", sa.Column("ui_trigger_source", run_trigger_source_enum, nullable=True))
    add_column_if_missing("ui_trigger_metadata", sa.Column("ui_trigger_metadata", sa.JSON(), nullable=True))
    add_column_if_missing("ui_triggered_at", sa.Column("ui_triggered_at", sa.DateTime(), nullable=True))
    add_column_if_missing("run_summary_message_id", sa.Column("run_summary_message_id", sa.String(), nullable=True))

    if dialect != "sqlite":
        op.create_foreign_key(
            "fk_crucible_runs_recommended_message",
            "crucible_runs",
            "crucible_messages",
            ["recommended_message_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_crucible_runs_summary_message",
            "crucible_runs",
            "crucible_messages",
            ["run_summary_message_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("crucible_runs")}

    if dialect != "sqlite":
        op.drop_constraint("fk_crucible_runs_summary_message", "crucible_runs", type_="foreignkey")
        op.drop_constraint("fk_crucible_runs_recommended_message", "crucible_runs", type_="foreignkey")

    def drop_column_if_exists(name: str) -> None:
        if name in existing_columns:
            op.drop_column("crucible_runs", name)
            existing_columns.remove(name)

    drop_column_if_exists("run_summary_message_id")
    drop_column_if_exists("ui_triggered_at")
    drop_column_if_exists("ui_trigger_metadata")
    drop_column_if_exists("ui_trigger_source")
    drop_column_if_exists("ui_trigger_id")
    drop_column_if_exists("recommended_config_snapshot")
    drop_column_if_exists("recommended_message_id")

    run_trigger_source_enum.drop(bind, checkfirst=True)


