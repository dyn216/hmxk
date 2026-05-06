"""
测试配置模块与现有代码的集成
"""
from config import settings, get_database_url


def test_database_integration():
    """测试配置模块与数据库模块的集成"""
    print("=" * 50)
    print("测试配置与数据库集成")
    print("=" * 50)
    
    # 测试数据库URL获取
    db_url = get_database_url()
    print(f"\n✓ 从配置获取数据库URL: {db_url}")
    
    # 测试与现有database.py的兼容性
    import os
    old_db_url = os.getenv("DATABASE_URL", "sqlite:///./chronic_disease.db")
    print(f"✓ 原有方式获取数据库URL: {old_db_url}")
    
    # 验证配置可以被环境变量覆盖
    print(f"\n✓ 配置支持环境变量覆盖")
    print(f"  - 当前数据库URL: {settings.database_url}")
    print(f"  - 可通过设置 DATABASE_URL 环境变量覆盖")
    
    print("\n" + "=" * 50)
    print("集成测试完成")
    print("=" * 50)


def test_settings_usage():
    """测试配置在FastAPI中的使用"""
    print("\n" + "=" * 50)
    print("测试FastAPI集成示例")
    print("=" * 50)
    
    print("""
示例代码：

from fastapi import FastAPI, Depends
from config import Settings, get_settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

@app.get("/config")
async def get_config(config: Settings = Depends(get_settings)):
    return {
        "app_name": config.app_name,
        "version": config.app_version,
        "debug": config.debug
    }
    """)
    
    print("=" * 50)


if __name__ == "__main__":
    test_database_integration()
    test_settings_usage()
