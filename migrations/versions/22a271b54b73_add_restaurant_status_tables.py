"""add restaurant status tables

Revision ID: 22a271b54b73
Revises: 
Create Date: 2023-11-26 17:30:19.162554

"""
from typing import Sequence, Union
from enum import Enum

from alembic import op
import sqlalchemy as sa


class Status(Enum):
    active = 1
    inactive = 2


# revision identifiers, used by Alembic.
revision: str = "22a271b54b73"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "store_timings",
        sa.Column("id", sa.BIGINT, primary_key=True, autoincrement=True),
        sa.Column("store_id", sa.BIGINT, index=True),
        sa.Column("day", sa.INT, nullable=False, index=True),
        sa.Column("start_time_local", sa.TIME, nullable=False),
        sa.Column("end_time_local", sa.TIME, nullable=False),
    )
    op.create_table(
        "store_pings",
        sa.Column("id", sa.BIGINT, primary_key=True, autoincrement=True),
        sa.Column("store_id", sa.BIGINT, nullable=False, index=True),
        sa.Column(
            "status",
            sa.Enum(Status),
            nullable=False,
            index=True,
            default=Status.active.name,
        ),
        sa.Column("timestamp_utc", sa.TIMESTAMP, nullable=False),
    )
    op.create_table(
        "store_timezones",
        sa.Column("store_id", sa.BIGINT, primary_key=True),
        sa.Column(
            "timezone_str", sa.VARCHAR(255), nullable=False, default="America/Chicago"
        ),
    )


def downgrade() -> None:
    op.drop_table("store_timings", info={"ifexists": True})
    op.drop_table("store_pings", info={"ifexists": True})
    op.drop_table("store_timezones", info={"ifexists": True})
