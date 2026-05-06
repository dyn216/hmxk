"""
测试日志系统
验证日志配置、处理器和轮转机制
"""
import os
import logging
import tempfile
from pathlib import Path
import sys

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logging_config import (
    setup_logging,
    get_logger,
    log_request,
    log_exception,
    log_database_operation,
    log_startup_info,
    log_shutdown_info,
    create_formatter,
    create_console_handler,
    create_rotating_file_handler
)


def test_setup_logging():
    """测试日志系统初始化"""
    print("\n=== 测试日志系统初始化 ===")
    
    # 创建临时日志文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_log_file = f.name
    
    try:
        # 初始化日志系统
        logger = setup_logging(log_level="DEBUG", log_file=temp_log_file)
        
        # 验证日志记录器已配置
        assert logger is not None
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 2  # 控制台 + 文件
        
        print("✓ 日志系统初始化成功")
        print(f"✓ 日志级别: {logging.getLevelName(logger.level)}")
        print(f"✓ 处理器数量: {len(logger.handlers)}")
        
        # 测试日志写入
        test_logger = get_logger("test")
        test_logger.debug("这是DEBUG日志")
        test_logger.info("这是INFO日志")
        test_logger.warning("这是WARNING日志")
        test_logger.error("这是ERROR日志")
        
        # 验证日志文件存在且有内容
        assert os.path.exists(temp_log_file)
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "这是DEBUG日志" in content
            assert "这是INFO日志" in content
            assert "这是WARNING日志" in content
            assert "这是ERROR日志" in content
        
        print("✓ 日志写入验证成功")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_log_file):
            os.remove(temp_log_file)


def test_log_formatter():
    """测试日志格式器"""
    print("\n=== 测试日志格式器 ===")
    
    formatter = create_formatter()
    assert formatter is not None
    
    # 创建测试日志记录
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="测试消息",
        args=(),
        exc_info=None,
        func="test_func"
    )
    
    formatted = formatter.format(record)
    
    # 验证格式包含必要信息
    assert "test" in formatted
    assert "INFO" in formatted
    assert "test.py:10" in formatted
    assert "test_func()" in formatted
    assert "测试消息" in formatted
    
    print("✓ 日志格式器验证成功")
    print(f"  格式化输出: {formatted}")


def test_console_handler():
    """测试控制台处理器"""
    print("\n=== 测试控制台处理器 ===")
    
    formatter = create_formatter()
    handler = create_console_handler(formatter)
    
    assert handler is not None
    assert handler.level == logging.INFO
    assert handler.formatter == formatter
    
    print("✓ 控制台处理器创建成功")
    print(f"✓ 日志级别: {logging.getLevelName(handler.level)}")


def test_rotating_file_handler():
    """测试轮转文件处理器"""
    print("\n=== 测试轮转文件处理器 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_log_file = f.name
    
    try:
        formatter = create_formatter()
        handler = create_rotating_file_handler(
            file_path=temp_log_file,
            formatter=formatter,
            max_bytes=1024,  # 1KB for testing
            backup_count=3
        )
        
        assert handler is not None
        assert handler.maxBytes == 1024
        assert handler.backupCount == 3
        assert handler.level == logging.DEBUG
        
        print("✓ 轮转文件处理器创建成功")
        print(f"✓ 最大文件大小: {handler.maxBytes} bytes")
        print(f"✓ 备份文件数量: {handler.backupCount}")
        
        # 测试日志轮转
        logger = logging.getLogger("rotation_test")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        # 写入大量日志触发轮转
        for i in range(100):
            logger.info(f"测试日志轮转 - 消息 {i} - " + "x" * 50)
        
        # 检查是否创建了备份文件
        log_dir = Path(temp_log_file).parent
        log_name = Path(temp_log_file).name
        backup_files = list(log_dir.glob(f"{log_name}.*"))
        
        print(f"✓ 日志轮转测试完成，创建了 {len(backup_files)} 个备份文件")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_log_file):
            os.remove(temp_log_file)
        # 清理备份文件
        log_dir = Path(temp_log_file).parent
        log_name = Path(temp_log_file).name
        for backup in log_dir.glob(f"{log_name}.*"):
            backup.unlink()


def test_log_request():
    """测试请求日志记录"""
    print("\n=== 测试请求日志记录 ===")
    
    # 测试不同状态码的日志
    log_request("GET", "/api/patient/profile", 200, 0.123, "127.0.0.1")
    log_request("POST", "/api/patient/login", 401, 0.056, "192.168.1.1")
    log_request("GET", "/api/admin/users", 500, 1.234, "10.0.0.1")
    
    print("✓ 请求日志记录成功")


def test_log_exception():
    """测试异常日志记录"""
    print("\n=== 测试异常日志记录 ===")
    
    try:
        # 触发一个异常
        raise ValueError("测试异常")
    except Exception as e:
        log_exception(e, context={"user_id": 123, "action": "test"})
    
    print("✓ 异常日志记录成功")


def test_log_database_operation():
    """测试数据库操作日志"""
    print("\n=== 测试数据库操作日志 ===")
    
    # 测试成功的操作
    log_database_operation("SELECT", "users", True, 0.012)
    log_database_operation("INSERT", "measurements", True, 0.034)
    
    # 测试失败的操作
    log_database_operation(
        "UPDATE", "patients", False, 0.056,
        error="Constraint violation"
    )
    
    print("✓ 数据库操作日志记录成功")


def test_log_startup_shutdown():
    """测试启动和关闭日志"""
    print("\n=== 测试启动和关闭日志 ===")
    
    log_startup_info("测试应用", "1.0.0", "0.0.0.0", 8000)
    log_shutdown_info()
    
    print("✓ 启动和关闭日志记录成功")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试日志系统")
    print("=" * 60)
    
    try:
        test_setup_logging()
        test_log_formatter()
        test_console_handler()
        test_rotating_file_handler()
        test_log_request()
        test_log_exception()
        test_log_database_operation()
        test_log_startup_shutdown()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
