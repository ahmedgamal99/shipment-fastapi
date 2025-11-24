"""fix shipment_tag fk

Revision ID: 20251114_fix_shipmenttag_fk
Revises: e2e1e0bf0f17
Create Date: 2025-11-14 23:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251114_fix_shipmenttag_fk"
down_revision: Union[str, Sequence[str], None] = "e2e1e0bf0f17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix `shipment_tag.tag_id` foreign key to point to `tag(id)`.

    This migration drops any existing constraint named
    `shipment_tag_tag_id_fkey` (if present) and re-creates it pointing to
    `tag(id)`. It is written defensively (IF EXISTS) so running it when the
    constraint is already correct is a no-op.
    """
    conn = op.get_bind()

    # Drop any possibly-wrong FK (no-op if missing)
    conn.execute(sa.text(
        "ALTER TABLE shipment_tag DROP CONSTRAINT IF EXISTS shipment_tag_tag_id_fkey"
    ))

    # Create the correct FK (won't run if a constraint with same name exists)
    conn.execute(sa.text(
        "ALTER TABLE shipment_tag ADD CONSTRAINT shipment_tag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES tag(id)"
    ))


def downgrade() -> None:
    """Revert the FK fix by dropping the constraint we created.

    Note: This downgrade will remove the constraint but will NOT recreate any
    previous (possibly incorrect) constraint. Restore that manually if you
    need to revert to the exact previous state.
    """
    conn = op.get_bind()
    conn.execute(sa.text(
        "ALTER TABLE shipment_tag DROP CONSTRAINT IF EXISTS shipment_tag_tag_id_fkey"
    ))
