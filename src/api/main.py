"""
FastAPI应用主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from loguru import logger

from .schemas.common import HealthResponse
from .routes import ppt_routes, file_routes
from ..models.response import APIResponse


# 应用启动和关闭事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 AIPPT API服务启动中...")
    start_time = time.time()
    app.state.start_time = start_time

    yield

    # 关闭时执行
    logger.info("👋 AIPPT API服务关闭中...")


# 创建FastAPI应用实例
app = FastAPI(
    title="AIPPT API",
    description="AI驱动的PowerPoint生成系统 - RESTful API接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    start_time = time.time()

    # 处理请求
    response = await call_next(request)

    # 计算处理时间
    process_time = time.time() - start_time

    # 记录日志
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    # 添加处理时间到响应头
    response.headers["X-Process-Time"] = str(process_time)

    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "data": {"detail": str(exc)} if logger.level == "DEBUG" else None
        }
    )


# 注册路由
app.include_router(
    ppt_routes.router,
    prefix="/api/v1/ppt",
    tags=["PPT"]
)

app.include_router(
    file_routes.router,
    prefix="/api/v1/files",
    tags=["Files"]
)


# 根路径
@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "name": "AIPPT API",
        "version": "1.0.0",
        "description": "AI驱动的PowerPoint生成系统",
        "docs": "/docs",
        "health": "/health"
    }


# 健康检查
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查接口"""
    uptime = time.time() - app.state.start_time

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=round(uptime, 2)
    )


# 启动说明
if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 启动AIPPT API服务...")
    logger.info("📖 API文档: http://localhost:8000/docs")
    logger.info("🔍 健康检查: http://localhost:8000/health")

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
