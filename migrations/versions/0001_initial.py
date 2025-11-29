"""Initial unified schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-02-15 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union
from uuid import uuid4

import sqlmodel
from alembic import op
import sqlalchemy as sa
from sqlalchemy import column, table
from sqlalchemy.dialects import postgresql

from app.database.models import ShipmentStatus, TagName

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables and seed the tag catalog."""
    op.create_table(
        "delivery_partner",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("max_handling_capacity", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "location",
        sa.Column("zip_code", sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("zip_code"),
    )

    op.create_table(
        "seller",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("address", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("zip_code", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tag",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Enum(TagName, name="tagname"), nullable=False),
        sa.Column("instruction", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "servicable_location",
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["location.zip_code"]),
        sa.ForeignKeyConstraint(["partner_id"], ["delivery_partner.id"]),
        sa.PrimaryKeyConstraint("partner_id", "location_id"),
    )

    op.create_table(
        "shipment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("client_contact_email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("client_contact_phone", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("destination", sa.Integer(), nullable=False),
        sa.Column("estimated_delivery", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delivery_partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["delivery_partner_id"], ["delivery_partner.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["seller.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "review",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("shipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipment.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shipment_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("location", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum(ShipmentStatus, name="shipmentstatus"), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("shipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipment.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shipment_tag",
        sa.Column("shipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipment.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"]),
        sa.PrimaryKeyConstraint("shipment_id", "tag_id"),
    )

    # Seed the tag catalog with the default instructions.
    instructions = {
        TagName.EXPRESS: "Prioritize expedited handling; use fastest route.",
        TagName.STANDARD: "Process under standard SLA and routing.",
        TagName.FRAGILE: "Handle with care; add cushioning; avoid stacking.",
        TagName.HEAVY: "Use lifting aid or team lift; verify weight limits.",
        TagName.INTERNATIONAL: "Verify customs docs and HS codes; apply duties.",
        TagName.DOMESTIC: "Use domestic routing and standard documentation.",
        TagName.TEMPERATURE_CONTROLLED: "Maintain required temperature; preserve cold chain.",
        TagName.GIFT: "Exclude pricing; include gift note; neutral packaging.",
        TagName.RETURN: "Attach RMA; route to returns center; inspect on receipt.",
        TagName.DOCUMENTS: "Use document pouch; do not fold; require signature.",
    }

    tags_table = table(
        "tag",
        column("id", postgresql.UUID(as_uuid=True)),
        column("name", sa.Enum(TagName, name="tagname")),
        column("instruction", sqlmodel.sql.sqltypes.AutoString()),
    )
    op.bulk_insert(
        tags_table,
        [
            {
                "id": uuid4(),
                "name": tag_name,
                "instruction": instruction,
            }
            for tag_name, instruction in instructions.items()
        ],
    )


def downgrade() -> None:
    """Drop all objects created in this revision."""
    op.drop_table("shipment_tag")
    op.drop_table("shipment_event")
    op.drop_table("review")
    op.drop_table("shipment")
    op.drop_table("servicable_location")
    op.drop_table("tag")
    op.drop_table("seller")
    op.drop_table("location")
    op.drop_table("delivery_partner")

    sa.Enum(ShipmentStatus, name="shipmentstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(TagName, name="tagname").drop(op.get_bind(), checkfirst=True)
