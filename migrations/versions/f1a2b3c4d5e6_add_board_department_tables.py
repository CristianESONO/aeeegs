"""Add board_term, board_member, department tables

Revision ID: f1a2b3c4d5e6
Revises: 460ee0ea6c52
Create Date: 2026-07-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '460ee0ea6c52'
branch_labels = None
depends_on = None


def upgrade():
    # Create department table
    op.create_table('department',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create board_term table
    op.create_table('board_term',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('start_year', sa.Integer(), nullable=False),
        sa.Column('end_year', sa.Integer(), nullable=False),
        sa.Column('president_name', sa.String(length=200), nullable=False),
        sa.Column('president_image', sa.String(length=100), nullable=True),
        sa.Column('president_bio', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create board_member table
    op.create_table('board_member',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('term_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('image_filename', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['term_id'], ['board_term.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['department.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('board_member')
    op.drop_table('board_term')
    op.drop_table('department')
