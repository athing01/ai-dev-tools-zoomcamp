"""Create tasks table and task_status enum.

Revision ID: 001
Revises:
Create Date: 2026-09-24 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the native PostgreSQL enum type for task status.
    op.execute(
        "CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'done')"
    )

    # Create the tasks table preserving the baseline logical contract:
    # id PK autoincrement; title NOT NULL; description NOT NULL default "";
    # status enum NOT NULL; created_at/updated_at timezone-aware UTC
    # timestamps with updated_at advancing on update.
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "status",
            postgresql.ENUM("todo", "in_progress", "done", name="task_status", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="tasks_pkey"),
    )


def downgrade() -> None:
    # Drop the tasks table and the enum type in reverse order.
    op.drop_table("tasks")
    op.execute("DROP TYPE task_status")