"""FastAPI 应用主入口"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db, engine
from .api import research, reports, chat, auth

settings = get_settings()

# 全局关闭标志
_shutdown_flag = False


def is_shutting_down() -> bool:
    """检查是否正在关闭"""
    return _shutdown_flag


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _shutdown_flag
    
    # 启动时初始化数据库
    await init_db()
    print("[OK] Database initialized")
    print("[OK] Server started - Press Ctrl+C to stop")
    
    try:
        yield
    finally:
        # 标记正在关闭
        _shutdown_flag = True
        print("\n[INFO] Shutting down...")
        
        # 关闭数据库连接
        await engine.dispose()
        print("[OK] Database connections closed")
        print("[OK] Shutdown complete")


# 创建 FastAPI 应用
app = FastAPI(
    title="上市公司深度研究 Agent 系统",
    description="基于 AI Agent 的上市公司深度研究系统，自动收集、分析信息并生成专业研究报告",
    version="0.1.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(research.router, prefix="/api", tags=["研究"])
app.include_router(reports.router, prefix="/api", tags=["报告"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])


@app.get("/")
async def root():
    """健康检查"""
    return {
        "message": "上市公司深度研究 Agent 系统",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "shutting_down": _shutdown_flag}
