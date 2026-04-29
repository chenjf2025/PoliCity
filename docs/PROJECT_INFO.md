# CGDSS 项目关键信息

## 项目概述

- **项目名称**: 城策城市治理决策支持平台 (City Governance Decision Support System)
- **项目简称**: CGDSS
- **代码仓库**: https://github.com/chenjf2025/PoliCity
- **开发日期**: 2026-04-30
- **版本**: v1.0.0

---

## 一、部署环境信息

### 1.1 生产服务器

| 项目 | 信息 |
|------|------|
| 服务器 IP | 192.168.71.127 |
| SSH 用户 | chenjf |
| SSH 密码 | chenjf |
| sudo 密码 | chenjf |
| 项目路径 | ~/cgdss |

### 1.2 服务端口

| 服务 | 容器端口 | 主机端口 | 访问地址 |
|------|---------|---------|---------|
| backend | 8000 | 8000 | http://192.168.71.127:8000 |
| frontend | 80 | 3001 | http://192.168.71.127:3001 |
| redis | 6379 | 6380 | 内网访问 |

### 1.3 数据库

| 项目 | 信息 |
|------|------|
| 类型 | PostgreSQL |
| 地址 | 192.168.71.127:5433 |
| 数据库名 | cgdss |
| 用户 | nexteacher |
| 密码 | nexteacher8018 |

---

## 二、第三方 API 配置

### 2.1 DeepSeek LLM

| 项目 | 信息 |
|------|------|
| API URL | https://api.deepseek.com/v1/chat/completions |
| API Key | sk-3edb33a0774d45f789feaa2bd18acb56 |
| Model | deepseek-chat |

### 2.2 Dify AI

| 项目 | 信息 |
|------|------|
| API URL | http://192.168.71.101:8080/v1 |
| API Key | app-drScqCHbwG0oUmh2TYqr6lnT |
| App ID | 46f69385-1556-4107-80f7-e0b0424a63cc |
| Dataset ID | f14f5c44-d420-442e-adaa-bf8c8887e75b |

---

## 三、Docker Compose 配置

### 3.1 docker-compose.yml 关键配置

```yaml
services:
  backend:
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://nexteacher:nexteacher8018@192.168.71.127:5433/cgdss
      REDIS_URL: redis://192.168.71.127:6380/0
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    ports:
      - "3001:80"

  redis:
    ports:
      - "6380:6379"
```

---

## 四、常用运维命令

### 4.1 服务管理

```bash
# SSH 登录
ssh chenjf@192.168.71.127

# 进入项目目录
cd ~/cgdss

# 查看服务状态
docker compose ps

# 重启后端
echo 'chenjf' | sudo -S docker compose restart backend

# 重启前端
echo 'chenjf' | sudo -S docker compose restart frontend

# 停止所有服务
docker compose down

# 启动所有服务
docker compose up -d

# 重新构建并部署
echo 'chenjf' | sudo -S docker compose up -d --build backend
echo 'chenjf' | sudo -S docker compose up -d --build frontend
```

### 4.2 日志查看

```bash
# 查看后端日志
docker compose logs backend

# 查看前端日志
docker compose logs frontend

# 实时跟踪日志
docker compose logs -f backend
```

### 4.3 代码同步与部署

```bash
# 本地修改代码后，同步到服务器
scp backend/app/services/llm.py chenjf@192.168.71.127:~/cgdss/backend/app/services/llm.py
scp backend/app/api/v1/dify.py chenjf@192.168.71.127:~/cgdss/backend/app/api/v1/dify.py
scp frontend/src/api/index.ts chenjf@192.168.71.127:~/cgdss/frontend/src/api/index.ts
scp frontend/src/views/ChatAssistant.vue chenjf@192.168.71.127:~/cgdss/frontend/src/views/ChatAssistant.vue

# 服务器上重新构建
ssh chenjf@192.168.71.127 "cd ~/cgdss && echo 'chenjf' | sudo -S docker compose up -d --build backend"
```

### 4.4 数据库操作

```bash
# 进入 PostgreSQL 容器
docker compose exec postgres psql -U nexteacher -d cgdss

# 常用 SQL
SELECT * FROM dict_indicator LIMIT 5;
SELECT COUNT(*) FROM data_raw_record;
SELECT COUNT(*) FROM data_evaluation;
```

---

## 五、API 接口文档

- API 文档: http://192.168.71.127:8000/docs
- 后端基础 URL: http://192.168.71.127:8000/api/v1

### 5.1 主要接口

| 模块 | 接口 | 方法 |
|------|------|------|
| 指标管理 | /api/v1/indicators | GET/POST |
| 数据采集 | /api/v1/data/raw | GET/POST |
| 标准化 | /api/v1/data/normalize | POST |
| 评价引擎 | /api/v1/evaluation/radar | GET |
| 政策仿真 | /api/v1/simulation/what-if | POST |
| Agent分析 | /api/v1/simulation/agent-analyze | POST |
| Dify对话 | /api/v1/dify/chat | POST |
| Dify流式 | /api/v1/dify/chat/stream | POST (SSE) |

---

## 六、数据模型

### 6.1 核心表结构

| 表名 | 说明 |
|------|------|
| dict_indicator | 43个指标字典 |
| data_raw_record | 原始数据记录 |
| data_standard_score | 标准化得分 |
| data_evaluation | 综合评价结果 |
| data_simulation_log | 仿真记录 |
| dict_benchmark_city | 对标城市 |

### 6.2 指标体系

- **经济活力 (E01-E10)**: 权重 25%
- **文化繁荣 (C01-C08)**: 权重 15%
- **人力资源 (H01-H08)**: 权重 20%
- **城乡融合 (U01-U08)**: 权重 20%
- **城市治理 (G01-G09)**: 权重 20%

### 6.3 标准化算法

```python
# 正向指标
P = (x - min) / (max - min) * 100

# 负向指标
P = (max - x) / (max - min) * 100
```

### 6.4 综合得分计算

```
S = Σ(Wi × Pi)
```

---

## 七、测试数据

### 7.1 测试数据生成

```bash
# 在服务器上执行
docker compose exec backend python /app/scripts/generate_test_data.py
```

### 7.2 测试地区

default, BJ(北京), SH(上海), GZ(广州), SZ(深圳), HZ(杭州), NJ(南京), WH(武汉), CD(成都), XA(西安)

### 7.3 测试年份

2020, 2021, 2022, 2023, 2024

---

## 八、技术栈

### 8.1 后端

- Python 3.10
- FastAPI 0.109.2
- SQLAlchemy 2.0.25
- PostgreSQL (psycopg2-binary 2.9.9)
- Redis 5.0.1
- httpx 0.26.0

### 8.2 前端

- Vue 3 + Composition API
- TypeScript
- Element Plus
- ECharts
- Vite 5.4.21
- marked (Markdown渲染)

### 8.3 基础设施

- Docker & Docker Compose
- Nginx
- PostgreSQL
- Redis

---

## 九、已知问题和限制

1. **下拉框时序问题**: 前端某些下拉框选择可能存在 API 时序问题
2. **Dify流式依赖网络**: 需要网络稳定才能保证流式响应流畅
3. **未实现用户认证**: 当前版本无用户登录功能

---

## 十、后续优化建议

- [ ] 添加用户认证和权限管理 (JWT)
- [ ] 实现 WebSocket 实时通信
- [ ] 添加数据导出功能 (Excel/PDF)
- [ ] 优化大数据量渲染性能
- [ ] 添加单元测试和集成测试
- [ ] 对标城市数据完善
- [ ] RAG 知识库完善

---

## 十一、关键文件路径

| 文件 | 说明 |
|------|------|
| backend/app/services/llm.py | DeepSeek LLM 服务 |
| backend/app/api/v1/dify.py | Dify AI 对话 API |
| backend/app/services/evaluator.py | 评价引擎 |
| backend/app/services/simulator.py | What-If 仿真器 |
| backend/app/services/agent/coordinator.py | Agent 协调器 |
| frontend/src/views/ChatAssistant.vue | AI 对话页面 |
| frontend/src/views/Simulation.vue | 政策仿真页面 |
| scripts/generate_test_data.py | 测试数据生成脚本 |

---

*最后更新: 2026-04-30*
