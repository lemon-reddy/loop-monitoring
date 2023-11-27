"""add reports table

Revision ID: 3b1b1afdc3ae
Revises: 22a271b54b73
Create Date: 2023-11-26 19:31:51.457963

"""
from typing import Sequence, Union
from enum import Enum

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3b1b1afdc3ae"
down_revision: Union[str, None] = "22a271b54b73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class JobStatus(Enum):
    pending = 0
    running = 1
    finished = 2
    failed = 3


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("report_id", sa.VARCHAR(16), primary_key=True),
        sa.Column(
            "status", sa.Enum(JobStatus), index=True, default=JobStatus.pending.name
        ),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("started_at", sa.TIMESTAMP, nullable=True),
        sa.Column("finished_at", sa.TIMESTAMP, nullable=True),
        sa.Column("filename", sa.VARCHAR(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("reports")
