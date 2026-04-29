# CGDSS 开发工作总结

## 项目信息
- **项目名称**: 城策城市治理决策支持平台 (CGDSS)
- **开发日期**: 2026-04-30
- **代码仓库**: https://github.com/chenjf2025/PoliCity

---

## 一、本次完成的功能开发

### 1.1 DeepSeek LLM 服务修复
**问题**: Agent 智能分析无法输出内容，报错 `__enter__`

**原因**: `httpx.AsyncClient` 在同步上下文中使用 context manager 模式不当

**解决方案**: 将异步客户端改为同步客户端

**修改文件**: `backend/app/services/llm.py`

```python
# 修改前 (有问题)
try:
    with httpx.AsyncClient(timeout=60.0) as client:
        response = client.post(self.api_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

# 修改后 (已修复)
try:
    client = httpx.Client(timeout=60.0)
    try:
        response = client.post(self.api_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    finally:
        client.close()
```

---

### 1.2 Dify AI 对话流式响应
**问题**: AI 助手回复需要等待很久才一次性显示，用户体验差

**解决方案**: 新增流式响应接口，使用 Server-Sent Events (SSE) 实时推送

**新增接口**: `POST /api/v1/dify/chat/stream`

**修改文件**:
- `backend/app/api/v1/dify.py` - 新增流式端点
- `frontend/src/api/index.ts` - 新增 `difyChatStream` 方法
- `frontend/src/views/ChatAssistant.vue` - 改造为流式读取

**后端实现**:
```python
@router.post("/chat/stream")
async def chat_with_dify_stream(request: ChatRequest, db: Session = Depends(get_db)):
    # 设置 response_mode: "streaming"
    payload = {
        "query": request.query,
        "user": request.user_id,
        "response_mode": "streaming",  # 流式模式
        "inputs": {"city_context": context}
    }

    async def stream_from_dify():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", dify_url, json=payload, headers=headers) as response:
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk

    return StreamingResponse(stream_from_dify(), media_type="text/event-stream")
```

**前端实现**:
```typescript
const response = await difyChatStream({ query, user_id: 'web_user' })
const reader = response.body?.getReader()
const decoder = new TextDecoder()

while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    // 处理 SSE 数据并实时更新 UI
}
```

---

### 1.3 部署到生产环境
**目标服务器**: 192.168.71.127
**部署方式**: Docker Compose

**部署步骤**:
```bash
# 1. 停止旧服务
docker compose down

# 2. 重新构建镜像 (应用新代码)
docker compose up -d --build backend
docker compose up -d --build frontend

# 3. 验证服务状态
docker compose ps
```

**服务端口映射**:
| 服务 | 容器端口 | 主机端口 | 状态 |
|------|---------|---------|------|
| backend | 8000 | 8000 | running |
| frontend | 80 | 3001 | running |
| redis | 6379 | 6380 | healthy |

---

### 1.4 代码推送至 GitHub
**仓库地址**: https://github.com/chenjf2025/PoliCity

**推送内容**:
- 51 个文件
- 5598 行代码
- 包含完整的前后端代码、Docker 配置、初始化脚本

---

## 二、项目完整功能清单

### 2.1 后端功能 (FastAPI)
| 模块 | 功能 | 状态 |
|------|------|------|
| 指标管理 API | CRUD 操作、维度汇总 | ✅ |
| 数据采集 API | Excel 导入、单条录入、标准化计算 | ✅ |
| 评价引擎 API | 雷达图数据、总分排名、历史趋势、短板预警 | ✅ |
| 政策仿真 API | What-If 仿真、历史记录、Agent 分析 | ✅ |
| 对标分析 API | 城市列表、对比分析 | ✅ |
| Dify AI API | 对话助手 (阻塞/流式双模式) | ✅ |
| Agent 多智能体 | Economy/Culture/Human/Policy Agent 协调器 | ✅ |

### 2.2 前端功能 (Vue3)
| 页面 | 功能 | 状态 |
|------|------|------|
| Dashboard | 雷达图、区域/年份选择器 | ✅ |
| Evaluation | 五维度详情、趋势图 | ✅ |
| Simulation | 政策仿真滑块、Agent 分析、Markdown 渲染 | ✅ |
| Benchmark | 对标城市对比 | ✅ |
| ChatAssistant | AI 对话助手 (流式响应) | ✅ |
| Indicators | 指标管理列表 | ✅ |

### 2.3 数据模型
| 表名 | 说明 | 状态 |
|------|------|------|
| dict_indicator | 43 个指标字典 | ✅ |
| data_raw_record | 原始数据记录 | ✅ |
| data_standard_score | 标准化得分 | ✅ |
| data_evaluation | 综合评价结果 | ✅ |
| data_simulation_log | 仿真记录 | ✅ |

---

## 三、部署与运维手册

### 3.1 服务器信息
| 项目 | 值 |
|------|---|
| 服务器 IP | 192.168.71.127 |
| SSH 用户 | chenjf |
| 项目路径 | ~/cgdss |
| 后端端口 | 8000 |
| 前端端口 | 3001 |
| Redis 端口 | 6380 |

### 3.2 远程管理命令

```bash
# SSH 登录
ssh chenjf@192.168.71.127

# 进入项目目录
cd ~/cgdss

# 查看服务状态
docker compose ps

# 查看后端日志
docker compose logs backend

# 查看前端日志
docker compose logs frontend

# 重启后端服务
echo 'chenjf' | sudo -S docker compose restart backend

# 重启前端服务
echo 'chenjf' | sudo -S docker compose restart frontend

# 重新构建并部署 (代码更新后)
echo 'chenjf' | sudo -S docker compose up -d --build backend
echo 'chenjf' | sudo -S docker compose up -d --build frontend

# 停止所有服务
docker compose down

# 启动所有服务
docker compose up -d
```

### 3.3 本地开发修改代码后部署流程

```bash
# 1. 本地修改代码

# 2. 同步代码到服务器
scp backend/app/services/llm.py chenjf@192.168.71.127:~/cgdss/backend/app/services/llm.py
scp backend/app/api/v1/dify.py chenjf@192.168.71.127:~/cgdss/backend/app/api/v1/dify.py
scp frontend/src/api/index.ts chenjf@192.168.71.127:~/cgdss/frontend/src/api/index.ts
scp frontend/src/views/ChatAssistant.vue chenjf@192.168.71.127:~/cgdss/frontend/src/views/ChatAssistant.vue

# 3. 在服务器上重新构建
ssh chenjf@192.168.71.127 "cd ~/cgdss && echo 'chenjf' | sudo -S docker compose up -d --build backend && echo 'chenjf' | sudo -S docker compose up -d --build frontend"
```

### 3.4 Git 开发流程

```bash
# 1. 克隆仓库
git clone https://github.com/chenjf2025/PoliCity.git

# 2. 创建开发分支
git checkout -b feature/xxx

# 3. 修改代码后提交
git add .
git commit -m "feat: xxx"

# 4. 推送到远程
git push origin feature/xxx

# 5. 在 GitHub 上创建 Pull Request
```

### 3.5 服务访问地址

| 服务 | 地址 |
|------|------|
| 前端页面 | http://192.168.71.127:3001 |
| 后端 API | http://192.168.71.127:8000 |
| API 文档 | http://192.168.71.127:8000/docs |

### 3.6 数据库连接

| 项目 | 值 |
|------|---|
| 类型 | PostgreSQL |
| 地址 | 192.168.71.127:5433 |
| 数据库 | cgdss |
| 用户 | nexteacher |
| 密码 | nexteacher8018 |

---

## 四、技术栈清单

### 后端
- Python 3.10
- FastAPI 0.109.2
- SQLAlchemy 2.0.25
- PostgreSQL (psycopg2-binary)
- Redis 5.0.1
- httpx 0.26.0
- DeepSeek API

### 前端
- Vue 3 + Composition API
- TypeScript
- Element Plus
- ECharts
- Vite
- marked (Markdown 渲染)

### 基础设施
- Docker & Docker Compose
- Nginx
- PostgreSQL
- Redis

---

## 五、已知问题和后续优化

### 5.1 已知问题
- 前端某些下拉框选择功能可能存在 API 时序问题
- Dify 流式响应需要网络稳定

### 5.2 后续优化建议
- [ ] 添加用户认证和权限管理
- [ ] 实现 WebSocket 实时通信
- [ ] 添加数据导出功能 (Excel/PDF)
- [ ] 优化大数据量下的渲染性能
- [ ] 添加单元测试和集成测试

---

## 六、版本记录

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0.0 | 2026-04-30 | 初始版本，包含完整功能 |

---

*文档生成时间: 2026-04-30*
