from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.api.health import router as health_router
from app.api.templates import router as templates_router
from app.api.tasks import router as tasks_router
from app.core.redis_client import redis_client
from app.core.database import init_db

settings = get_settings()

# API限流中间件
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# 注册限流
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router)
app.include_router(templates_router)
app.include_router(tasks_router)


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"OpenMOSS: {settings.OPENMOSS_BASE_URL}")
    print(f"OpenClaw: {settings.OPENCLAW_BASE_URL}")
    
    # 初始化数据库
    await init_db()
    print("Database initialized")
    
    # 连接 Redis
    if redis_client.connect():
        print(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    else:
        print("Warning: Redis connection failed")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    redis_client.disconnect()
    print("Shutting down...")