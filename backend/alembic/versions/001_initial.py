"""Initial migration - create all existing tables

Revision ID: 001_initial
Revises:
Create Date: 2026-04-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 dict_indicator 表
    op.create_table(
        'dict_indicator',
        sa.Column('indicator_code', sa.String(10), primary_key=True),
        sa.Column('dimension', sa.String(20), nullable=False),
        sa.Column('dimension_cn', sa.String(20), nullable=False),
        sa.Column('indicator_name', sa.String(100), nullable=False),
        sa.Column('indicator_name_en', sa.String(100)),
        sa.Column('weight', sa.Float, nullable=False),
        sa.Column('polarity', sa.Integer, nullable=False),
        sa.Column('unit', sa.String(20)),
        sa.Column('data_source', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.Integer, default=1),
        sa.Column('version', sa.String(20), default="1.0"),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'))
    )

    # 创建 data_raw_record 表（包含新字段）
    op.create_table(
        'data_raw_record',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('region_code', sa.String(20), nullable=False),
        sa.Column('region_name', sa.String(50), nullable=False),
        sa.Column('indicator_code', sa.String(10), sa.ForeignKey('dict_indicator.indicator_code'), nullable=False),
        sa.Column('report_year', sa.Integer, nullable=False),
        sa.Column('report_month', sa.Integer),
        sa.Column('raw_value', sa.Float, nullable=False),
        sa.Column('data_status', sa.Integer, default=1),
        sa.Column('source_name', sa.String(200)),
        sa.Column('source_url', sa.String(500)),
        sa.Column('is_deleted', sa.Integer, default=0),
        sa.Column('created_by', sa.String(50)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        sa.UniqueConstraint('region_code', 'indicator_code', 'report_year', 'report_month', name='uq_raw_data')
    )

    # 创建 data_standard_score 表
    op.create_table(
        'data_standard_score',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('region_code', sa.String(20), nullable=False),
        sa.Column('region_name', sa.String(50), nullable=False),
        sa.Column('indicator_code', sa.String(10), sa.ForeignKey('dict_indicator.indicator_code'), nullable=False),
        sa.Column('report_year', sa.Integer, nullable=False),
        sa.Column('report_month', sa.Integer),
        sa.Column('raw_value', sa.Float, nullable=False),
        sa.Column('min_value', sa.Float),
        sa.Column('max_value', sa.Float),
        sa.Column('standard_score', sa.Float, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.UniqueConstraint('region_code', 'indicator_code', 'report_year', 'report_month', name='uq_standard_score')
    )

    # 创建 data_evaluation 表
    op.create_table(
        'data_evaluation',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('region_code', sa.String(20), nullable=False),
        sa.Column('region_name', sa.String(50), nullable=False),
        sa.Column('report_year', sa.Integer, nullable=False),
        sa.Column('report_month', sa.Integer),
        sa.Column('economic_score', sa.Float),
        sa.Column('culture_score', sa.Float),
        sa.Column('human_score', sa.Float),
        sa.Column('urban_score', sa.Float),
        sa.Column('governance_score', sa.Float),
        sa.Column('total_score', sa.Float),
        sa.Column('city_rank', sa.Integer),
        sa.Column('province_rank', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'))
    )

    # 创建 data_simulation_log 表
    op.create_table(
        'data_simulation_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(50)),
        sa.Column('region_code', sa.String(20), nullable=False),
        sa.Column('region_name', sa.String(50)),
        sa.Column('simulation_name', sa.String(100)),
        sa.Column('params', JSONB, nullable=False),
        sa.Column('original_total_score', sa.Float),
        sa.Column('simulated_total_score', sa.Float),
        sa.Column('score_delta', sa.Float),
        sa.Column('rank_change', sa.Integer),
        sa.Column('agent_analysis', JSONB),
        sa.Column('analysis_report', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'))
    )

    # 创建 dict_benchmark_city 表
    op.create_table(
        'dict_benchmark_city',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('city_code', sa.String(20), unique=True, nullable=False),
        sa.Column('city_name', sa.String(50), nullable=False),
        sa.Column('province', sa.String(50)),
        sa.Column('city_level', sa.String(20)),
        sa.Column('population', sa.Float),
        sa.Column('gdp', sa.Float),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'))
    )

    # 创建 sys_user 表
    op.create_table(
        'sys_user',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('phone', sa.String(20), unique=True),
        sa.Column('email', sa.String(100), unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100)),
        sa.Column('role', sa.String(20), default="user"),
        sa.Column('is_active', sa.Integer, default=1),
        sa.Column('must_change_password', sa.Integer, default=0),
        sa.Column('last_login', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'))
    )

    # 创建 sys_operation_log 表
    op.create_table(
        'sys_operation_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(50)),
        sa.Column('username', sa.String(50)),
        sa.Column('action', sa.String(50)),
        sa.Column('detail', sa.Text),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'))
    )

    # 创建 config_anomaly_rule 表
    op.create_table(
        'config_anomaly_rule',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('indicator_code', sa.String(10), sa.ForeignKey('dict_indicator.indicator_code'), nullable=False),
        sa.Column('min_value', sa.Float),
        sa.Column('max_value', sa.Float),
        sa.Column('max_fluctuation', sa.Float),
        sa.Column('description', sa.String(500)),
        sa.Column('status', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        sa.UniqueConstraint('indicator_code', name='uq_anomaly_rule')
    )

    # 创建 data_anomaly_record 表
    op.create_table(
        'data_anomaly_record',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('raw_data_id', UUID(as_uuid=True), sa.ForeignKey('data_raw_record.id'), nullable=False),
        sa.Column('indicator_code', sa.String(10), nullable=False),
        sa.Column('region_code', sa.String(20), nullable=False),
        sa.Column('region_name', sa.String(50)),
        sa.Column('report_year', sa.Integer, nullable=False),
        sa.Column('report_month', sa.Integer),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('anomaly_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(20), default="PENDING"),
        sa.Column('confirmed_by', sa.String(50)),
        sa.Column('confirmed_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'))
    )


def downgrade() -> None:
    op.drop_table('data_anomaly_record')
    op.drop_table('config_anomaly_rule')
    op.drop_table('sys_operation_log')
    op.drop_table('sys_user')
    op.drop_table('dict_benchmark_city')
    op.drop_table('data_simulation_log')
    op.drop_table('data_evaluation')
    op.drop_table('data_standard_score')
    op.drop_table('data_raw_record')
    op.drop_table('dict_indicator')
