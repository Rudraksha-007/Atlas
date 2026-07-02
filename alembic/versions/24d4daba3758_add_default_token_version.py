"""add_default_token_version

Revision ID: 24d4daba3758
Revises: f3b4c7a4e462
Create Date: 2026-07-02 18:00:46.407340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24d4daba3758'
down_revision: Union[str, Sequence[str], None] = 'f3b4c7a4e462'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
