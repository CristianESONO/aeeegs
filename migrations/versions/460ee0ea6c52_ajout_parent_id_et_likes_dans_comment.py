"""Ajout parent_id et likes dans Comment

Revision ID: 460ee0ea6c52
Revises: e02c4a261e1c
Create Date: 2025-06-26 05:17:41.773737

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '460ee0ea6c52'
down_revision = 'e02c4a261e1c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('post_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('username', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('date_posted', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('likes', sa.Integer(), nullable=True))
        batch_op.alter_column('content',
               existing_type=sa.TEXT(),
               nullable=False)
        # Supprime cette ligne:
        # batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('fk_comment_post', 'article', ['post_id'], ['id'])
        batch_op.create_foreign_key('fk_comment_parent', 'comment', ['parent_id'], ['id'])
        batch_op.drop_column('created_at')
        batch_op.drop_column('article_id')

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('article_id', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), nullable=True))
        # Supprimer ces lignes :
        # batch_op.drop_constraint(None, type_='foreignkey')
        # batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('fk_comment_article', 'article', ['article_id'], ['id'])
        batch_op.alter_column('content',
               existing_type=sa.TEXT(),
               nullable=True)
        batch_op.drop_column('likes')
        batch_op.drop_column('date_posted')
        batch_op.drop_column('username')
        batch_op.drop_column('parent_id')
        batch_op.drop_column('post_id')


    # ### end Alembic commands ###
