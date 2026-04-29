"""
城策城市治理决策支持平台 - FastAPI后端入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import indicator, data, evaluation, simulation, benchmark, dify

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="城市治理决策支持平台API - 提供指标管理、数据采集、评价引擎、政策仿真、对标分析等能力"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(indicator.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(benchmark.router, prefix="/api/v1")
app.include_router(dify.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
