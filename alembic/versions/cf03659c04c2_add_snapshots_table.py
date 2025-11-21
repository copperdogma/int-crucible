"""add_snapshots_table

Revision ID: cf03659c04c2
Revises: a3d1c7e53b34
Create Date: 2025-11-21 11:34:40.462592

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'cf03659c04c2'
down_revision = 'a3d1c7e53b34'
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists."""
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Create crucible_snapshots table
    if not _table_exists(inspector, 'crucible_snapshots'):
        op.create_table(
            'crucible_snapshots',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('tags', sa.JSON(), nullable=True),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('run_id', sa.String(), nullable=True),
            sa.Column('snapshot_data', sa.JSON(), nullable=False),
            sa.Column('reference_metrics', sa.JSON(), nullable=True),
            sa.Column('invariants', sa.JSON(), nullable=True),
            sa.Column('version', sa.String(), nullable=False, server_default='1.0'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
            sa.ForeignKeyConstraint(['project_id'], ['crucible_projects.id'], ondelete='CASCADE'),
        )
        
        # Create indexes
        op.create_index('ix_crucible_snapshots_project_id', 'crucible_snapshots', ['project_id'])
        op.create_index('ix_crucible_snapshots_name', 'crucible_snapshots', ['name'])
        
        # Note: For PostgreSQL, we could add a GIN index on tags for JSON array search,
        # but SQLite doesn't support GIN indexes, so we'll skip for cross-database compatibility


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    if _table_exists(inspector, 'crucible_snapshots'):
        op.drop_index('ix_crucible_snapshots_name', table_name='crucible_snapshots')
        op.drop_index('ix_crucible_snapshots_project_id', table_name='crucible_snapshots')
        op.drop_table('crucible_snapshots')

