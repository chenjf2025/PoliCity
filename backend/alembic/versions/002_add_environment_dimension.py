"""Add environment dimension - 6th dimension for ecological environment

Revision ID: 002_add_environment_dimension
Revises: 001_initial
Create Date: 2026-05-04

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_environment_dimension'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 在 data_evaluation 表新增 environment_score 字段
    op.add_column(
        'data_evaluation',
        sa.Column('environment_score', sa.Float, nullable=True)
    )

    # 为 dict_indicator 表添加 is_observation 字段（分两步：先 nullable，再设置默认值，最后改为 NOT NULL）
    op.add_column(
        'dict_indicator',
        sa.Column('is_observation', sa.Integer, nullable=True)
    )

    # 更新现有记录的 is_observation 为 0
    op.execute("UPDATE dict_indicator SET is_observation = 0 WHERE is_observation IS NULL")

    # 改为 NOT NULL
    op.alter_column('dict_indicator', 'is_observation', nullable=False)


def downgrade() -> None:
    op.drop_column('data_evaluation', 'environment_score')
    op.drop_column('dict_indicator', 'is_observation')
