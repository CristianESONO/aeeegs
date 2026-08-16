"""Add contact_info table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-08-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('contact_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('whatsapp_url', sa.String(length=300), nullable=True),
        sa.Column('facebook_url', sa.String(length=300), nullable=True),
        sa.Column('instagram_url', sa.String(length=300), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('contact_info')
