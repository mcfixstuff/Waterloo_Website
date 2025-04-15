"""empty message

Revision ID: bc2b64947cf2
Revises: 9e59330794c2
Create Date: 2025-03-18 19:18:11.380071

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc2b64947cf2'
down_revision = '9e59330794c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### Skip table creation as it already exists ###
    pass


def downgrade():
    # ### Skip table deletion as it's handled by another migration ###
    pass
