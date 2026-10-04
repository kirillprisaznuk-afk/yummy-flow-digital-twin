"""Initial scenario snapshot schema. Deliberately contains no business defaults."""

import sqlalchemy as sa
from alembic import op

revision = "0001_scenarios"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scenarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(2000), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scenarios_created_at", "scenarios", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_scenarios_created_at", table_name="scenarios")
    op.drop_table("scenarios")
