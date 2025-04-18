"""add category_id to Cost

Revision ID: add_category_id
Revises: 
Create Date: 2025-04-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_category_id'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('cost', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_cost_category_id', 'cost', 'cost_category', ['category_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_cost_category_id', 'cost', type_='foreignkey')
    op.drop_column('cost', 'category_id')
