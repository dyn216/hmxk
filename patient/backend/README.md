# 慢性病管理小程序后端API

## 项目简介

这是一个基于FastAPI开发的慢性病管理系统后端，为三个微信小程序（患者端、医生端、管理端）提供完整的API服务。

### 主要功能

#### 患者端 API (`/api/patient`)
- 用户登录认证
- 个人档案管理
- 监测数据记录（血压、血糖、心率等）
- AI智能分析和健康建议
- 用药管理和提醒
- 监护人管理
- 设备绑定

#### 医生端 API (`/api/doctor`)
- 医生登录认证
- 患者列表管理
- 患者监测数据查看
- 消息通讯
- 视频问诊管理
- 随访计划
- 新闻动态

#### 管理端 API (`/api/admin`)
- 管理员登录
- 统计数据面板
- 用户管理（患者、医生、管理员）
- 设备管理
- 新闻管理
- 系统日志
- KPI考核指标

## 技术栈

- **框架**: FastAPI 0.115.0
- **数据库**: SQLite（开发环境）/ MySQL（生产环境）
- **ORM**: SQLAlchemy 2.0.36
- **认证**: JWT (PyJWT)
- **数据验证**: Pydantic 2.9.2

## 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装步骤

#### Windows系统

1. 双击运行 `start.bat`
2. 脚本会自动：
   - 创建虚拟环境
   - 安装依赖包
   - 初始化数据库（首次运行）
   - 启动服务

#### Linux/Mac系统

1. 添加执行权限：
```bash
chmod +x start.sh
```

2. 运行启动脚本：
```bash
./start.sh
```

#### 手动安装

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python init_db.py

# 5. 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 访问地址

- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 测试账号

| 角色 | 手机号 | 密码 |
|------|--------|------|
| 管理员 | 13800000000 | admin123 |
| 医生1 | 13800000001 | doctor123 |
| 医生2 | 13800000002 | doctor123 |
| 患者1 | 13900000001 | patient123 |
| 患者2 | 13900000002 | patient123 |
| 患者3 | 13900000003 | patient123 |

## 数据库结构

### 核心数据表

- **users**: 用户基础表（统一管理所有用户）
- **patient_profiles**: 患者档案表
- **doctor_profiles**: 医生档案表
- **admin_profiles**: 管理员档案表
- **measurements**: 监测数据表
- **medications**: 用药管理表
- **guardians**: 监护人表
- **devices**: 设备管理表
- **messages**: 消息表
- **consultations**: 问诊记录表
- **follow_ups**: 随访计划表
- **news**: 新闻动态表
- **system_logs**: 系统日志表

## API接口示例

### 患者登录

```http
POST /api/patient/login
Content-Type: application/json

{
  "phone": "13900000001",
  "password": "patient123"
}
```

### 创建监测数据

```http
POST /api/patient/measurements?user_id=1
Content-Type: application/json

{
  "type": "bp",
  "value1": 135,
  "value2": 85,
  "measured_at": "2024-01-20T08:30:00"
}
```

响应会包含AI分析结果：
```json
{
  "id": 1,
  "patient_id": 1,
  "type": "bp",
  "value1": 135,
  "value2": 85,
  "measured_at": "2024-01-20T08:30:00",
  "risk_level": "normal",
  "ai_suggestion": "血压正常偏高，建议注意饮食..."
}
```

## AI功能

### 血压分析
- 根据中国高血压防治指南2023
- 自动判断风险等级：normal / warning / danger
- 提供个性化健康建议

### 血糖分析
- 区分空腹、餐后、随机血糖
- 糖尿病前期预警
- 饮食运动建议

### 心率分析
- 正常/偏低/偏高判断
- 异常情况提醒

## 部署说明

### 生产环境配置

1. **数据库切换**
   - 修改 `database.py` 中的 `DATABASE_URL`
   - 从SQLite切换到MySQL/PostgreSQL

2. **安全配置**
   - 修改 `utils.py` 中的 `SECRET_KEY`
   - 配置CORS允许的域名
   - 启用HTTPS

3. **性能优化**
   - 使用Gunicorn作为WSGI服务器
   - 配置Nginx反向代理
   - 启用数据库连接池

### Docker部署

```dockerfile
# 待补充 Dockerfile
```

## 开发规范

### 代码规范
- 遵循PEP 8
- 使用类型提示
- 添加docstring文档

### API规范
- RESTful设计
- 统一错误处理
- 返回标准JSON格式

### 数据库规范
- 使用外键约束
- 添加索引优化查询
- 记录时间戳

## 常见问题

### 1. 数据库连接错误
检查数据库URL配置，确保数据库服务已启动

### 2. 端口被占用
修改启动命令中的端口号：`--port 8001`

### 3. 依赖安装失败
尝试使用国内镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 项目结构

```
backend/
├── main.py                 # 主程序入口
├── database.py             # 数据库配置
├── models.py               # 数据模型
├── schemas.py              # Pydantic模型
├── utils.py                # 工具函数
├── init_db.py              # 数据库初始化
├── requirements.txt        # 依赖包
├── start.sh               # Linux启动脚本
├── start.bat              # Windows启动脚本
├── README.md              # 项目文档
└── routers/               # API路由
    ├── patient_api.py     # 患者端API
    ├── doctor_api.py      # 医生端API
    └── admin_api.py       # 管理端API
```

## 更新日志

### v1.0.0 (2024-01-20)
- 完成患者端、医生端、管理端完整API
- 实现AI健康分析功能
- 添加数据库初始化脚本
- 创建测试数据

## 联系方式

如有问题，请联系开发团队。

## 许可证

本项目仅供学习和内部使用。
