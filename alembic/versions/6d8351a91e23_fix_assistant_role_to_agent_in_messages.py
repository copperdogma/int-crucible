"""fix_assistant_role_to_agent_in_messages

Revision ID: 6d8351a91e23
Revises: e900a34872ac
Create Date: 2025-11-21 23:08:29.404244

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision = '6d8351a91e23'
down_revision = 'e900a34872ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix existing messages with 'assistant' or lowercase roles to use uppercase enum values."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if crucible_messages table exists
    if 'crucible_messages' not in inspector.get_table_names():
        return
    
    # The database enum expects uppercase: USER, SYSTEM, AGENT
    # But some messages may have lowercase values. Fix all of them.
    
    # Convert 'assistant' -> 'AGENT' (if any exist)
    bind.execute(text("UPDATE crucible_messages SET role = 'AGENT' WHERE role = 'assistant'"))
    
    # Convert lowercase values to uppercase to match enum
    bind.execute(text("UPDATE crucible_messages SET role = 'USER' WHERE role = 'user'"))
    bind.execute(text("UPDATE crucible_messages SET role = 'SYSTEM' WHERE role = 'system'"))
    bind.execute(text("UPDATE crucible_messages SET role = 'AGENT' WHERE role = 'agent'"))
    
    bind.commit()


def downgrade() -> None:
    """Note: This migration is not reversible as 'assistant' is not a valid enum value."""
    # We cannot safely downgrade this as 'assistant' is not in the MessageRole enum
    # If we need to downgrade, we'd need to first add 'assistant' to the enum,
    # which would require schema changes beyond this migration
    pass

