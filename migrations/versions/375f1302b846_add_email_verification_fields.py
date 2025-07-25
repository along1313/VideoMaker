"""add email verification fields

Revision ID: 375f1302b846
Revises: 7688d262bbc4
Create Date: 2025-06-30 09:09:50.424725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '375f1302b846'
down_revision = '7688d262bbc4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_email_verified', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('email_verification_token', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('email_verification_sent_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('password_reset_token', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('password_reset_sent_at', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password_reset_sent_at')
        batch_op.drop_column('password_reset_token')
        batch_op.drop_column('email_verification_sent_at')
        batch_op.drop_column('email_verification_token')
        batch_op.drop_column('is_email_verified')

    # ### end Alembic commands ###
