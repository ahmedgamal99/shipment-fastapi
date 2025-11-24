"""Add serviceable_zip_codes to delivery_partner

Revision ID: 4da6f77986c3
Revises: 8a5f31623591
Create Date: 2025-11-14 21:07:23.956831

"""
from typing import Sequence, Union
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4da6f77986c3'
down_revision: Union[str, Sequence[str], None] = '8a5f31623591'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
