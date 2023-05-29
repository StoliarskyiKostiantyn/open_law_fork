"""remove fields from section and interpretation

Revision ID: 883298018384
Revises: 5df1fabbee7d
Create Date: 2023-05-18 15:49:20.145655

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "883298018384"
down_revision = "5df1fabbee7d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("interpretations", schema=None) as batch_op:
        batch_op.drop_column("label")

    with op.batch_alter_table("sections", schema=None) as batch_op:
        batch_op.drop_column("about")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("sections", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("about", sa.TEXT(), autoincrement=False, nullable=True)
        )

    with op.batch_alter_table("interpretations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "label", sa.VARCHAR(length=256), autoincrement=False, nullable=False
            )
        )

    # ### end Alembic commands ###
