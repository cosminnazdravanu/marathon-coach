"""…

Revision ID: a355ff7741ce
Revises: b3fbee3dffbd
Create Date: 2025-08-07 13:12:32.781579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a355ff7741ce'
down_revision: Union[str, Sequence[str], None] = 'b3fbee3dffbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # Recreate the table and copy data under the hood
        with op.batch_alter_table("training_plan", recreate="always") as batch_op:
            # Keep this minimal. SQLite treats TEXT/VARCHAR/String the same, so
            # we really only need to change what matters.
            batch_op.alter_column(
                "date",
                existing_type=sa.Integer(),
                type_=sa.String(),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "type",
                existing_type=sa.Text(),
                nullable=True,  # keep the nullability change
            )
            # You can drop these if you want—they’re TEXT→String no-ops on SQLite.
            # batch_op.alter_column("warmup_target", existing_type=sa.Text(), type_=sa.String())
            # batch_op.alter_column("main_target", existing_type=sa.Text(), type_=sa.String())
            # batch_op.alter_column("cooldown_target", existing_type=sa.Text(), type_=sa.String())
            # batch_op.alter_column("terrain", existing_type=sa.Text(), type_=sa.String())

        # We already removed the bad "ALTER COLUMN id" earlier—no need to touch `id`.
    else:
        # Non-SQLite backends can alter in place
        op.alter_column("date", "training_plan",
                        existing_type=sa.Integer(), type_=sa.String(), existing_nullable=False)
        op.alter_column("type", "training_plan",
                        existing_type=sa.Text(), type_=sa.String(), nullable=True)
        # Optional: keep the other type changes if your other DB supports them.
        # op.alter_column(... warmup_target/main_target/cooldown_target/terrain ...)

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("training_plan", recreate="always") as batch_op:
            batch_op.alter_column(
                "date",
                existing_type=sa.String(),
                type_=sa.Integer(),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "type",
                existing_type=sa.String(),
                nullable=False,
            )
    else:
        op.alter_column("date", "training_plan",
                        existing_type=sa.String(), type_=sa.Integer(), existing_nullable=False)
        op.alter_column("type", "training_plan",
                        existing_type=sa.String(), type_=sa.Text(), nullable=False)
