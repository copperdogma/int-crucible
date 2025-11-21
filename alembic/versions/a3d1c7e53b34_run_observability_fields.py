"""Add run observability fields.

Revision ID: a3d1c7e53b34
Revises: 6a9abf0029cd
Create Date: 2025-11-21 15:45:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision = "a3d1c7e53b34"
down_revision = "6a9abf0029cd"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect = bind.dialect.name

    table = "crucible_runs"

    if not _has_column(inspector, table, "duration_seconds"):
        op.add_column(
            table,
            sa.Column("duration_seconds", sa.Float(), nullable=True),
        )

    for col_name in ("candidate_count", "scenario_count", "evaluation_count"):
        if not _has_column(inspector, table, col_name):
            op.add_column(
                table,
                sa.Column(col_name, sa.Integer(), nullable=False, server_default="0"),
            )

    if not _has_column(inspector, table, "metrics"):
        op.add_column(
            table,
            sa.Column("metrics", sa.JSON(), nullable=True),
        )

    if not _has_column(inspector, table, "llm_usage"):
        op.add_column(
            table,
            sa.Column("llm_usage", sa.JSON(), nullable=True),
        )

    if not _has_column(inspector, table, "error_summary"):
        op.add_column(
            table,
            sa.Column("error_summary", sa.Text(), nullable=True),
        )

    # Normalize NULL counters to 0 for existing rows
    op.execute(
        text(
            "UPDATE crucible_runs "
            "SET candidate_count = COALESCE(candidate_count, 0), "
            "    scenario_count = COALESCE(scenario_count, 0), "
            "    evaluation_count = COALESCE(evaluation_count, 0)"
        )
    )

    # Remove server defaults where supported (SQLite keeps defaults automatically)
    if dialect != "sqlite":
        for col_name in ("candidate_count", "scenario_count", "evaluation_count"):
            op.alter_column(
                table,
                col_name,
                existing_type=sa.Integer(),
                server_default=None,
                existing_nullable=False,
            )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    table = "crucible_runs"

    for col_name in (
        "error_summary",
        "llm_usage",
        "metrics",
        "evaluation_count",
        "scenario_count",
        "candidate_count",
        "duration_seconds",
    ):
        if _has_column(inspector, table, col_name):
            op.drop_column(table, col_name)

