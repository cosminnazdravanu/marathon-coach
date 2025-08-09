"""add users + auth_identities

Revision ID: eb6e65e88d5e
Revises: a355ff7741ce
Create Date: 2025-08-08 22:57:40.860436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb6e65e88d5e'
down_revision: Union[str, Sequence[str], None] = 'a355ff7741ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("avatar_url", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    # Optional index (unique already creates an index, but this keeps it explicit)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "auth_identities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String, nullable=False),          # "google" | "apple" | "facebook" | "strava"
        sa.Column("provider_user_id", sa.String, nullable=False),  # e.g. Google 'sub' / Strava athlete.id
        sa.Column("email_from_provider", sa.String, nullable=True),
        sa.Column("access_token_enc", sa.Text, nullable=True),
        sa.Column("refresh_token_enc", sa.Text, nullable=True),
        sa.Column("expires_at", sa.Integer, nullable=True),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_auth_identity"),
    )

# --- downgrade ---
def downgrade() -> None:
    op.drop_table("auth_identities")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
