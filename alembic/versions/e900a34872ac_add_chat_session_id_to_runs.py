"""add_chat_session_id_to_runs

Revision ID: e900a34872ac
Revises: cf03659c04c2
Create Date: 2025-11-21 16:17:31.583057

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'e900a34872ac'
down_revision = 'cf03659c04c2'
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:
    """Add chat_session_id column to crucible_runs table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    table = "crucible_runs"
    
    if not _has_column(inspector, table, "chat_session_id"):
        op.add_column(
            table,
            sa.Column("chat_session_id", sa.String(), nullable=True),
        )
        # Add foreign key constraint (SQLite may not enforce, but PostgreSQL will)
        try:
            op.create_foreign_key(
                "fk_runs_chat_session_id",
                table,
                "crucible_chat_sessions",
                ["chat_session_id"],
                ["id"],
            )
        except Exception:
            # SQLite may not support adding FK constraints after table creation
            # This is acceptable - the relationship is still valid in the ORM
            pass


def downgrade() -> None:
    """Remove chat_session_id column from crucible_runs table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    table = "crucible_runs"
    
    # Try to drop foreign key constraint first (if it exists)
    try:
        op.drop_constraint("fk_runs_chat_session_id", table, type_="foreignkey")
    except Exception:
        pass  # Constraint may not exist or may not be supported
    
    if _has_column(inspector, table, "chat_session_id"):
        op.drop_column(table, "chat_session_id")

