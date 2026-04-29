# 城策 - 城市治理决策支持平台 (CGDSS)

## 项目简介

城策城市治理决策支持平台是一个集数据采集、标准化评价、趋势监测与政策仿真于一体的智慧化管理平台。

## 功能特性

- **五大维度评价体系**: 经济活力、文化繁荣、人力资源、城乡融合、城市治理
- **43个三级指标**: 完整的指标管理和数据采集能力
- **极差标准化处理**: Min-Max标准化算法
- **AHP层次分析法**: 科学权重分配
- **政策仿真模拟器**: What-If情景分析
- **Agent多智能体**: AI驱动的政策分析
- **Dify集成**: AI对话助手

## 快速部署

### 前置要求

- Docker & Docker Compose
- PostgreSQL 14+
- Redis 7+

### 启动服务

```bash
# 克隆项目
cd /path/to/cgdss

# 启动所有服务
docker-compose up -d

# 初始化数据库（创建表）
docker exec cgdss-backend python -c "from app.core.database import engine, Base; Base.metadata.create_all(bind=engine)"

# 初始化指标数据
docker exec cgdss-backend python /app/scripts/init_indicators.py
```

### 访问服务

- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 目录结构

```
cgdss/
├── backend/              # FastAPI后端
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   ├── services/    # 业务逻辑
│   │   └── main.py      # 入口文件
│   ├── scripts/         # 初始化脚本
│   └── requirements.txt
├── frontend/            # Vue3前端
│   ├── src/
│   │   ├── api/        # API调用
│   │   ├── components/ # 组件
│   │   ├── views/      # 页面
│   │   └── router/     # 路由
│   └── package.json
├── docker-compose.yml   # 部署编排
└── README.md
```

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/v1/indicators | GET | 获取指标列表 |
| /api/v1/evaluation/radar | GET | 获取雷达图数据 |
| /api/v1/simulation/what-if | POST | What-If仿真 |
| /api/v1/benchmark/compare | POST | 对标分析 |
| /api/v1/dify/chat | POST | AI对话 |

## 配置说明

### 后端环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | PostgreSQL连接URL | postgresql://cgdss:cgdss123@postgres:5432/cgdss |
| REDIS_URL | Redis连接URL | redis://redis:6379/0 |
| DIFY_API_URL | Dify API地址 | http://192.168.71.101:8080/v1 |
| DIFY_API_KEY | Dify API Key | app-drScqCHbwG0oUmh2TYqr6lnT |

## 技术栈

- **后端**: Python 3.10+ / FastAPI / SQLAlchemy / Pandas
- **前端**: Vue 3 / Element Plus / ECharts
- **数据库**: PostgreSQL 14 / Redis 7
- **AI**: Dify / Agent Multi-Agent
- **部署**: Docker Compose
