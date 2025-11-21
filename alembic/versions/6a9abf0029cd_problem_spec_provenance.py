"""Add provenance_log to ProblemSpec.

Revision ID: 6a9abf0029cd
Revises: 5c7b9a3e3c5a
Create Date: 2025-11-21 09:40:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "6a9abf0029cd"
down_revision = "5c7b9a3e3c5a"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("crucible_problem_specs")}

    if "provenance_log" not in columns:
        op.add_column(
            "crucible_problem_specs",
            sa.Column("provenance_log", sa.JSON(), nullable=True),
        )

        dialect = bind.dialect.name
        if dialect == "postgresql":
            op.execute(
                sa.text(
                    "UPDATE crucible_problem_specs "
                    "SET provenance_log = '[]'::jsonb "
                    "WHERE provenance_log IS NULL"
                )
            )
        else:
            op.execute(
                sa.text(
                    "UPDATE crucible_problem_specs "
                    "SET provenance_log = '[]' "
                    "WHERE provenance_log IS NULL"
                )
            )

        if dialect != "sqlite":
            op.alter_column(
                "crucible_problem_specs",
                "provenance_log",
                existing_type=sa.JSON(),
                nullable=False,
            )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("crucible_problem_specs")}

    if "provenance_log" in columns:
        op.drop_column("crucible_problem_specs", "provenance_log")


