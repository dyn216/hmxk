"""
配置管理模块
使用Pydantic Settings从环境变量加载配置
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    应用配置类
    从环境变量或.env文件加载配置
    """
    
    # 应用基础配置
    app_name: str = "慢性病管理小程序后端API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库配置
    database_url: str = "sqlite:///./chronic_disease.db"
    
    # JWT认证配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7天
    
    # CORS配置
    cors_origins: list = ["*"]  # 生产环境应配置具体域名
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # 文件上传配置
    upload_max_size: int = 10 * 1024 * 1024  # 10MB
    upload_allowed_extensions: list = [".jpg", ".jpeg", ".png", ".pdf"]
    upload_dir: str = "uploads"
    
    # 数据库备份配置
    backup_dir: str = "backups"
    backup_retention_days: int = 30
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # 允许从环境变量覆盖配置
        # 例如: DATABASE_URL=mysql://... 会覆盖 database_url
        env_prefix = ""


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取配置实例
    用于FastAPI依赖注入
    
    Returns:
        Settings: 配置实例
    """
    return settings


def is_production() -> bool:
    """
    判断是否为生产环境
    
    Returns:
        bool: True表示生产环境，False表示开发环境
    """
    return not settings.debug


def get_database_url() -> str:
    """
    获取数据库连接URL
    
    Returns:
        str: 数据库连接URL
    """
    return settings.database_url


def ensure_directories():
    """
    确保必要的目录存在
    创建日志、上传、备份等目录
    """
    directories = [
        os.path.dirname(settings.log_file),
        settings.upload_dir,
        settings.backup_dir
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


# 初始化时确保目录存在
ensure_directories()
