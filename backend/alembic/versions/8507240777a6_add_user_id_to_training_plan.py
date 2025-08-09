"""add user_id to training_plan

Revision ID: 8507240777a6
Revises: facd5735c1af
Create Date: 2025-08-09 00:25:33.513195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "<PUT_NEW_REVISION_ID_HERE>"
down_revision: Union[str, Sequence[str], None] = "facd5735c1af"  # <-- your last head; adjust if different
branch_labels = None
depends_on = None

def upgrade() -> None:
    # SQLite-safe: add nullable column, then index
    with op.batch_alter_table("training_plan") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_training_plan_user_id", "training_plan", ["user_id"])

    # Optional: if you KNOW there's only one user, you can backfill like:
    # op.execute("UPDATE training_plan SET user_id = 1")

def downgrade() -> None:
    op.drop_index("ix_training_plan_user_id", table_name="training_plan")
    with op.batch_alter_table("training_plan") as batch:
        batch.drop_column("user_id")
