"""
日志配置模块
配置应用程序的日志系统，包括控制台和文件日志处理器
"""
import logging
import logging.handlers
import os
import sys
from typing import Optional
from config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None
) -> logging.Logger:
    """
    设置应用程序日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        max_bytes: 日志文件最大字节数
        backup_count: 备份文件数量
        
    Returns:
        logging.Logger: 配置好的日志器
    """
    # 使用配置文件中的默认值
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file
    max_bytes = max_bytes or settings.log_max_bytes
    backup_count = backup_count or settings.log_backup_count
    
    # 创建根日志器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建日志格式器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 详细格式器（用于文件日志）
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. 文件处理器（带轮转）
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # 3. 错误文件处理器（只记录ERROR及以上级别）
    if log_file:
        error_log_file = log_file.replace('.log', '_error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称，通常使用 __name__
        
    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)


def log_request(method: str, path: str, status_code: int, response_time: float, user_id: Optional[int] = None):
    """
    记录API请求日志
    
    Args:
        method: HTTP方法
        path: 请求路径
        status_code: 响应状态码
        response_time: 响应时间（秒）
        user_id: 用户ID（可选）
    """
    logger = get_logger("api.request")
    
    # 构建日志消息
    message = f"{method} {path} - {status_code} - {response_time:.3f}s"
    if user_id:
        message += f" - user_id: {user_id}"
    
    # 根据状态码选择日志级别
    if status_code >= 500:
        logger.error(message)
    elif status_code >= 400:
        logger.warning(message)
    else:
        logger.info(message)


def log_database_operation(operation: str, table: str, record_id: Optional[int] = None, error: Optional[str] = None):
    """
    记录数据库操作日志
    
    Args:
        operation: 操作类型 (CREATE, READ, UPDATE, DELETE)
        table: 表名
        record_id: 记录ID（可选）
        error: 错误信息（可选）
    """
    logger = get_logger("database")
    
    message = f"{operation} {table}"
    if record_id:
        message += f" - id: {record_id}"
    
    if error:
        logger.error(f"{message} - ERROR: {error}")
    else:
        logger.info(message)


def log_authentication(action: str, user_id: Optional[int] = None, phone: Optional[str] = None, success: bool = True, error: Optional[str] = None):
    """
    记录认证相关日志
    
    Args:
        action: 操作类型 (LOGIN, LOGOUT, TOKEN_REFRESH, etc.)
        user_id: 用户ID（可选）
        phone: 手机号（可选，会被部分遮掩）
        success: 是否成功
        error: 错误信息（可选）
    """
    logger = get_logger("auth")
    
    # 遮掩手机号中间4位
    masked_phone = None
    if phone and len(phone) >= 7:
        masked_phone = phone[:3] + "****" + phone[-4:]
    
    message = f"{action}"
    if user_id:
        message += f" - user_id: {user_id}"
    if masked_phone:
        message += f" - phone: {masked_phone}"
    
    if success:
        logger.info(f"{message} - SUCCESS")
    else:
        error_msg = f"{message} - FAILED"
        if error:
            error_msg += f" - {error}"
        logger.warning(error_msg)


def log_ai_analysis(measurement_type: str, values: dict, risk_level: str, processing_time: float):
    """
    记录AI分析日志
    
    Args:
        measurement_type: 监测数据类型
        values: 监测值
        risk_level: 风险等级
        processing_time: 处理时间（秒）
    """
    logger = get_logger("ai.analysis")
    
    message = f"AI分析 - {measurement_type} - 风险等级: {risk_level} - 处理时间: {processing_time:.3f}s - 数值: {values}"
    logger.info(message)


def log_system_event(event: str, details: Optional[dict] = None):
    """
    记录系统事件日志
    
    Args:
        event: 事件名称
        details: 事件详情（可选）
    """
    logger = get_logger("system")
    
    message = f"系统事件: {event}"
    if details:
        message += f" - 详情: {details}"
    
    logger.info(message)


# 初始化日志系统
def init_logging():
    """
    初始化日志系统
    在应用启动时调用
    """
    logger = setup_logging()
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {settings.log_level}")
    logger.info(f"日志文件: {settings.log_file}")
    return logger


# 为了向后兼容，提供一个默认的日志器
default_logger = None

def get_default_logger() -> logging.Logger:
    """
    获取默认日志器
    如果还未初始化，则先初始化
    """
    global default_logger
    if default_logger is None:
        default_logger = init_logging()
    return default_logger