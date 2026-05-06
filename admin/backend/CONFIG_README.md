# 配置管理模块使用说明

## 概述

配置管理模块 (`config.py`) 提供了统一的配置管理功能，支持从环境变量和 `.env` 文件加载配置。

## 快速开始

### 1. 创建配置文件

复制 `.env.example` 文件为 `.env`：

```bash
cp .env.example .env
```

### 2. 修改配置

编辑 `.env` 文件，根据实际环境修改配置项：

```bash
# 开发环境
DEBUG=true
LOG_LEVEL=DEBUG

# 生产环境
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/chronic_disease
```

### 3. 使用配置

在代码中导入并使用配置：

```python
from config import settings, get_settings

# 直接使用全局配置实例
print(settings.app_name)
print(settings.database_url)

# 或通过依赖注入（推荐用于FastAPI）
from fastapi import Depends

@app.get("/info")
async def get_info(config: Settings = Depends(get_settings)):
    return {"app_name": config.app_name}
```

## 配置项说明

### 应用基础配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `APP_NAME` | str | 慢性病管理小程序后端API | 应用名称 |
| `APP_VERSION` | str | 1.0.0 | 应用版本 |
| `DEBUG` | bool | false | 调试模式 |

### 服务器配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `HOST` | str | 0.0.0.0 | 服务器监听地址 |
| `PORT` | int | 8000 | 服务器监听端口 |

### 数据库配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABASE_URL` | str | sqlite:///./chronic_disease.db | 数据库连接URL |

支持的数据库：
- SQLite: `sqlite:///./database.db`
- MySQL: `mysql+pymysql://user:pass@host:port/dbname`
- PostgreSQL: `postgresql://user:pass@host:port/dbname`

### JWT认证配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `JWT_SECRET_KEY` | str | your-secret-key-change-in-production | JWT密钥（生产环境必须修改） |
| `JWT_ALGORITHM` | str | HS256 | JWT算法 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | int | 10080 | JWT令牌过期时间（分钟） |

### CORS配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `CORS_ORIGINS` | list | ["*"] | 允许的跨域来源 |

### 日志配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `LOG_LEVEL` | str | INFO | 日志级别 |
| `LOG_FILE` | str | logs/app.log | 日志文件路径 |
| `LOG_MAX_BYTES` | int | 10485760 | 日志文件最大大小（字节） |
| `LOG_BACKUP_COUNT` | int | 5 | 日志文件备份数量 |

### 文件上传配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `UPLOAD_MAX_SIZE` | int | 10485760 | 文件上传最大大小（字节） |
| `UPLOAD_ALLOWED_EXTENSIONS` | list | [".jpg", ".jpeg", ".png", ".pdf"] | 允许的文件扩展名 |
| `UPLOAD_DIR` | str | uploads | 文件上传目录 |

### 数据库备份配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `BACKUP_DIR` | str | backups | 备份文件存储目录 |
| `BACKUP_RETENTION_DAYS` | int | 30 | 备份文件保留天数 |

## 工具函数

### `get_settings()`

获取配置实例，用于FastAPI依赖注入。

```python
from fastapi import Depends
from config import Settings, get_settings

@app.get("/config")
async def get_config(config: Settings = Depends(get_settings)):
    return {"debug": config.debug}
```

### `is_production()`

判断是否为生产环境。

```python
from config import is_production

if is_production():
    print("运行在生产环境")
else:
    print("运行在开发环境")
```

### `get_database_url()`

获取数据库连接URL。

```python
from config import get_database_url

db_url = get_database_url()
```

### `ensure_directories()`

确保必要的目录存在（自动调用）。

```python
from config import ensure_directories

ensure_directories()  # 创建 logs/, uploads/, backups/ 目录
```

## 环境变量优先级

配置加载优先级（从高到低）：

1. 环境变量
2. `.env` 文件
3. 默认值

示例：

```bash
# 通过环境变量覆盖配置
export DEBUG=true
export PORT=8001

# 启动应用
python main.py
```

## 最佳实践

### 开发环境

```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./chronic_disease.db
```

### 生产环境

```bash
# .env
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/chronic_disease
JWT_SECRET_KEY=your-very-strong-secret-key-here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 安全建议

1. **永远不要提交 `.env` 文件到版本控制系统**
2. **生产环境必须修改 `JWT_SECRET_KEY`**
3. **生产环境必须配置具体的 `CORS_ORIGINS`**
4. **使用强密码保护数据库连接**
5. **定期更新密钥和密码**

## 测试

运行配置测试脚本：

```bash
cd backend
python test_config.py
```

## 故障排查

### 配置未生效

1. 检查 `.env` 文件是否存在
2. 检查环境变量名称是否正确（不区分大小写）
3. 检查配置值的数据类型是否正确

### 目录创建失败

1. 检查文件系统权限
2. 检查路径是否有效
3. 手动创建目录：`mkdir logs uploads backups`

### 数据库连接失败

1. 检查 `DATABASE_URL` 格式是否正确
2. 检查数据库服务是否运行
3. 检查用户名和密码是否正确
4. 检查网络连接

## 相关文件

- `config.py` - 配置管理模块
- `.env.example` - 配置模板文件
- `.env` - 实际配置文件（不提交到版本控制）
- `test_config.py` - 配置测试脚本
