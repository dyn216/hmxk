"""
简单测试脚本，验证配置模块功能
"""
from config import settings, get_settings, is_production, get_database_url, ensure_directories
import os


def test_config_loading():
    """测试配置加载"""
    print("=" * 50)
    print("测试配置模块")
    print("=" * 50)
    
    # 测试基础配置
    print(f"\n✓ 应用名称: {settings.app_name}")
    print(f"✓ 应用版本: {settings.app_version}")
    print(f"✓ 调试模式: {settings.debug}")
    
    # 测试服务器配置
    print(f"\n✓ 服务器地址: {settings.host}:{settings.port}")
    
    # 测试数据库配置
    print(f"\n✓ 数据库URL: {get_database_url()}")
    
    # 测试JWT配置
    print(f"\n✓ JWT算法: {settings.jwt_algorithm}")
    print(f"✓ JWT过期时间: {settings.jwt_access_token_expire_minutes} 分钟")
    
    # 测试日志配置
    print(f"\n✓ 日志级别: {settings.log_level}")
    print(f"✓ 日志文件: {settings.log_file}")
    
    # 测试文件上传配置
    print(f"\n✓ 上传最大大小: {settings.upload_max_size / 1024 / 1024} MB")
    print(f"✓ 允许的扩展名: {settings.upload_allowed_extensions}")
    
    # 测试环境判断
    print(f"\n✓ 是否生产环境: {is_production()}")
    
    # 测试目录创建
    print("\n检查必要目录:")
    directories = [
        os.path.dirname(settings.log_file),
        settings.upload_dir,
        settings.backup_dir
    ]
    
    for directory in directories:
        if directory and os.path.exists(directory):
            print(f"✓ {directory}/ 存在")
        else:
            print(f"✗ {directory}/ 不存在")
    
    print("\n" + "=" * 50)
    print("配置模块测试完成")
    print("=" * 50)


if __name__ == "__main__":
    test_config_loading()
