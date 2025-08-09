"""add users + auth_identities

Revision ID: facd5735c1af
Revises: eb6e65e88d5e
Create Date: 2025-08-08 23:03:52.278235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'facd5735c1af'
down_revision: Union[str, Sequence[str], None] = 'eb6e65e88d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if "users" not in tables:
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
    else:
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_idx ON users(email)")

    if "auth_identities" not in tables:
        op.create_table(
            "auth_identities",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("provider", sa.String, nullable=False),
            sa.Column("provider_user_id", sa.String, nullable=False),
            sa.Column("email_from_provider", sa.String, nullable=True),
            sa.Column("access_token_enc", sa.Text, nullable=True),
            sa.Column("refresh_token_enc", sa.Text, nullable=True),
            sa.Column("expires_at", sa.Integer, nullable=True),
            sa.UniqueConstraint("provider", "provider_user_id", name="uq_auth_identity"),
        )