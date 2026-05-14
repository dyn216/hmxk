from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import time
import logging
from contextlib import asynccontextmanager

from routers import patient_api, doctor_api, admin_api, upload_api
from config import settings
from logging_config import init_logging, log_request, log_system_event, get_logger
from database import engine, Base
import models  # noqa: F401  确保所有模型被注册到 Base.metadata

# 启动时按需创建新表（已存在的表不会被覆盖）
try:
    Base.metadata.create_all(bind=engine)
except Exception as _e:  # 仅记录，不阻断启动
    logging.getLogger(__name__).warning("create_all skipped: %s", _e)

# 初始化日志系统
logger = init_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    log_system_event("应用启动", {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "host": settings.host,
        "port": settings.port
    })
    logger.info(f"应用启动完成 - {settings.app_name} v{settings.app_version}")
    
    yield
    
    # 关闭事件
    log_system_event("应用关闭")
    logger.info("应用关闭完成")


app = FastAPI(
    title=settings.app_name,
    description="提供患者端、医生端、管理端的完整API服务",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS配置：使用配置文件中的设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求的日志"""
    start_time = time.time()
    
    # 获取用户ID（如果存在）
    user_id = None
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        # 这里可以解析JWT获取用户ID，暂时跳过
        pass
    
    # 处理请求
    response = await call_next(request)
    
    # 计算响应时间
    process_time = time.time() - start_time
    
    # 记录请求日志
    log_request(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        response_time=process_time,
        user_id=user_id
    )
    
    # 添加响应时间头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 三个子系统入口：患者 / 医生 / 管理端
app.include_router(patient_api.router, prefix="/api/patient", tags=["患者端"])
app.include_router(doctor_api.router, prefix="/api/doctor", tags=["医生端"])
app.include_router(admin_api.router, prefix="/api/admin", tags=["管理端"])

# 文件上传：三端共用，路径以 /api/upload 暴露；同时三端 prefix 兼容
app.include_router(upload_api.router, prefix="/api/upload", tags=["上传"])
app.include_router(upload_api.router, prefix="/api/patient/upload", tags=["上传-患者"])
app.include_router(upload_api.router, prefix="/api/doctor/upload", tags=["上传-医生"])
app.include_router(upload_api.router, prefix="/api/admin/upload", tags=["上传-管理"])

# 上传文件静态访问：上传后的相对路径形如 /uploads/image/20260101/xxx.png
_UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")


@app.get("/")
async def root():
    """根路径，返回API信息"""
    logger.info("访问根路径")
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "debug": settings.debug,
        "endpoints": {
            "患者端": "/api/patient",
            "医生端": "/api/doctor",
            "管理端": "/api/admin",
            "API文档": "/docs",
            "健康检查": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 这里可以添加数据库连接检查等
        # 暂时返回基本的健康状态
        health_status = {
            "status": "ok",
            "message": "服务运行正常",
            "timestamp": time.time(),
            "version": settings.app_version,
            "debug": settings.debug
        }
        
        logger.debug("健康检查通过")
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "error",
            "message": "服务异常",
            "timestamp": time.time()
        }


# 运行：
#   uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 
# 测试账号：
#   管理员：13800000000 / admin123
#   医生：13800000001 / doctor123
#   患者：13900000001 / patient123
