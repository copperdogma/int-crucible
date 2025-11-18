"""add_profiling_tables

Revision ID: dc24ead48293
Revises: fb9e61f33cbf
Create Date: 2025-11-12 23:27:58.269488

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dc24ead48293'
down_revision = 'fb9e61f33cbf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add profiling tables for performance monitoring."""

    # Create execution_profiles table
    op.create_table(
        'execution_profiles',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('experiment_id', sa.String(length=36), nullable=True),
        sa.Column('profile_type', sa.String(length=50), nullable=False),  # experiment, agent, workflow
        sa.Column('profiling_mode', sa.String(length=20), nullable=False),  # light, standard, full

        # Timing metrics
        sa.Column('execution_time', sa.Float(), nullable=False),
        sa.Column('cpu_time', sa.Float(), nullable=False),
        sa.Column('wall_time', sa.Float(), nullable=False),

        # Memory metrics
        sa.Column('memory_peak_mb', sa.Float(), nullable=False),
        sa.Column('memory_start_mb', sa.Float(), nullable=False),
        sa.Column('memory_end_mb', sa.Float(), nullable=False),
        sa.Column('memory_allocated_mb', sa.Float(), nullable=False),

        # Profiler overhead
        sa.Column('profiler_overhead_ms', sa.Float(), nullable=False, default=0.0),

        # Timestamps
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),

        # Additional data (stored as JSON)
        sa.Column('function_calls', sa.JSON(), nullable=True),
        sa.Column('function_times', sa.JSON(), nullable=True),
        sa.Column('bottlenecks', sa.JSON(), nullable=True),
        sa.Column('memory_snapshots', sa.JSON(), nullable=True),
        sa.Column('profile_data', sa.Text(), nullable=True),  # Raw cProfile output

        # Metadata
        sa.Column('metadata', sa.JSON(), nullable=True),
    )

    # Create indexes for fast querying
    op.create_index(
        'idx_execution_profiles_experiment_id',
        'execution_profiles',
        ['experiment_id'],
        unique=False
    )
    op.create_index(
        'idx_execution_profiles_profile_type',
        'execution_profiles',
        ['profile_type'],
        unique=False
    )
    op.create_index(
        'idx_execution_profiles_created_at',
        'execution_profiles',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'idx_execution_profiles_execution_time',
        'execution_profiles',
        ['execution_time'],
        unique=False
    )
    op.create_index(
        'idx_execution_profiles_memory_peak',
        'execution_profiles',
        ['memory_peak_mb'],
        unique=False
    )

    # Composite index for common queries
    op.create_index(
        'idx_execution_profiles_type_created',
        'execution_profiles',
        ['profile_type', 'created_at'],
        unique=False
    )
    op.create_index(
        'idx_execution_profiles_exp_created',
        'execution_profiles',
        ['experiment_id', 'created_at'],
        unique=False
    )

    # Create bottlenecks table for detailed analysis
    op.create_table(
        'profiling_bottlenecks',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('profile_id', sa.String(length=36), nullable=False),

        # Bottleneck details
        sa.Column('function_name', sa.String(length=255), nullable=False),
        sa.Column('module_name', sa.String(length=255), nullable=False),
        sa.Column('cumulative_time', sa.Float(), nullable=False),
        sa.Column('time_percent', sa.Float(), nullable=False),
        sa.Column('call_count', sa.Integer(), nullable=False),
        sa.Column('per_call_time', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),  # critical, high, medium, low

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),

        # Foreign key
        sa.ForeignKeyConstraint(
            ['profile_id'],
            ['execution_profiles.id'],
            ondelete='CASCADE'
        )
    )

    # Create indexes for bottlenecks
    op.create_index(
        'idx_profiling_bottlenecks_profile_id',
        'profiling_bottlenecks',
        ['profile_id'],
        unique=False
    )
    op.create_index(
        'idx_profiling_bottlenecks_severity',
        'profiling_bottlenecks',
        ['severity'],
        unique=False
    )
    op.create_index(
        'idx_profiling_bottlenecks_time_percent',
        'profiling_bottlenecks',
        ['time_percent'],
        unique=False
    )
    op.create_index(
        'idx_profiling_bottlenecks_function',
        'profiling_bottlenecks',
        ['function_name'],
        unique=False
    )


def downgrade() -> None:
    """Remove profiling tables."""

    # Drop indexes first
    op.drop_index('idx_profiling_bottlenecks_function', table_name='profiling_bottlenecks')
    op.drop_index('idx_profiling_bottlenecks_time_percent', table_name='profiling_bottlenecks')
    op.drop_index('idx_profiling_bottlenecks_severity', table_name='profiling_bottlenecks')
    op.drop_index('idx_profiling_bottlenecks_profile_id', table_name='profiling_bottlenecks')

    op.drop_index('idx_execution_profiles_exp_created', table_name='execution_profiles')
    op.drop_index('idx_execution_profiles_type_created', table_name='execution_profiles')
    op.drop_index('idx_execution_profiles_memory_peak', table_name='execution_profiles')
    op.drop_index('idx_execution_profiles_execution_time', table_name='execution_profiles')
    op.drop_index('idx_execution_profiles_created_at', table_name='execution_profiles')
    op.drop_index('idx_execution_profiles_profile_type', table_name='execution_profiles')
    op.drop_index('idx_execution_profiles_experiment_id', table_name='execution_profiles')

    # Drop tables
    op.drop_table('profiling_bottlenecks')
    op.drop_table('execution_profiles')
