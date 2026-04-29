from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.health import router as health_router
from app.api.templates import router as templates_router
from app.api.tasks import router as tasks_router
from app.core.redis_client import redis_client
from app.core.database import init_db
from app.core.sync_engine import sync_engine
from app.core.template_loader import TemplateLoader
import asyncio
import os

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（启动 + 关闭）"""
    # === 启动阶段 ===
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"OpenMOSS: {settings.OPENMOSS_BASE_URL}")
    print(f"OpenClaw: {settings.OPENCLAW_BASE_URL}")
    
    # 初始化数据库（允许失败，测试环境可能无 DB）
    try:
        await init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Continuing startup (may be test environment)")
    
    # 连接 Redis
    try:
        if redis_client.connect():
            print(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        else:
            print("Warning: Redis connection failed")
    except Exception as e:
        print(f"Warning: Redis connection error: {e}")
    
    # 启动 TemplateLoader（定时轮询模板目录）
    template_loader = TemplateLoader(settings.TEMPLATE_DIR)
    if await template_loader.start():
        print(f"TemplateLoader started, watching {settings.TEMPLATE_DIR}")
    else:
        print("Warning: TemplateLoader failed to start")
    
    # 启动 SyncEngine 后台循环（状态同步引擎）
    sync_task = asyncio.create_task(sync_engine.start_sync_loop())
    print(f"SyncEngine started, interval: {sync_engine.sync_interval}s")
    
    yield
    
    # === 关闭阶段 ===
    print("Shutting down...")
    
    # 停止 TemplateLoader
    try:
        await template_loader.stop()
        print("TemplateLoader stopped")
    except Exception as e:
        print(f"Warning: Error stopping TemplateLoader: {e}")
    
    # 取消 SyncEngine 后台任务
    try:
        sync_task.cancel()
        await sync_task
    except asyncio.CancelledError:
        print("SyncEngine stopped")
    except Exception as e:
        print(f"Warning: Error stopping SyncEngine: {e}")
    
    # 断开 Redis
    try:
        redis_client.disconnect()
        print("Redis disconnected")
    except Exception as e:
        print(f"Warning: Redis disconnect error: {e}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS中间件（ARCH-005 修复：生产环境应限制域名）
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router)
app.include_router(templates_router)
app.include_router(tasks_router)