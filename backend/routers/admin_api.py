from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_, case
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import (
    User, PatientProfile, DoctorProfile, AdminProfile,
    Measurement, Device, News, SystemLog, FollowUp,
    ShopProduct, ShopOrder, ShopOrderItem, Prescription, PrescriptionItem,
    UserRole, MeasurementType
)
from schemas import (
    LoginRequest, LoginResponse,
    UserOut, UserCreate, UserUpdate,
    UserStatusUpdate, AdminUserUpdate,
    DashboardStats, KPIStats,
    DeviceOut, DeviceCreate, DeviceUpdate,
    NewsCreate, NewsUpdate, NewsOut,
    ProductCreate, ProductUpdate, ShopProductOut,
    ShopOrderOut, ShopOrderShip,
    PrescriptionOut, PrescriptionUpdate,
    PatientDetail, DoctorDetail, AdminPatientUpdate, AdminDoctorUpdate
)
from utils import verify_password, create_access_token, hash_password, get_current_user_id

router = APIRouter()


# ============= 认证相关 =============

@router.post("/login", response_model=LoginResponse)
def admin_login(body: LoginRequest, db: Session = Depends(get_db)):
    """管理员登录"""
    user = db.query(User).filter(
        User.phone == body.phone,
        User.role == UserRole.ADMIN
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if body.password and not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="密码错误")
    
    if not user.status:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.commit()
    
    # 创建token
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    
    return LoginResponse(
        token=token,
        user_id=user.id,
        role=user.role,
        name=user.name,
        avatar=user.avatar
    )


# ============= 统计数据相关 =============

@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取管理后台统计数据"""
    # 总用户数
    total_users = db.query(User).count()
    
    # 患者数
    total_patients = db.query(User).filter(User.role == UserRole.PATIENT).count()
    
    # 医生数
    total_doctors = db.query(User).filter(User.role == UserRole.DOCTOR).count()
    
    # 监测数据总数
    total_measurements = db.query(Measurement).count()
    
    # 今日活跃用户（最近24小时登录）
    active_users_today = db.query(User).filter(
        User.last_login >= datetime.now() - timedelta(days=1)
    ).count()
    
    # 今日新增用户
    new_users_today = db.query(User).filter(
        User.created_at >= datetime.now() - timedelta(days=1)
    ).count()
    
    # 在线设备数
    online_devices = db.query(Device).filter(Device.status == "online").count()
    
    # 设备总数
    total_devices = db.query(Device).count()
    
    return DashboardStats(
        total_users=total_users,
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_measurements=total_measurements,
        active_users_today=active_users_today,
        new_users_today=new_users_today,
        online_devices=online_devices,
        total_devices=total_devices
    )


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    """获取管理后台统计数据"""
    return get_dashboard_stats(db)


def measurement_type_label(measurement_type) -> str:
    value = getattr(measurement_type, "name", str(measurement_type))
    labels = {
        "BLOOD_PRESSURE": "血压",
        "BLOOD_SUGAR": "血糖",
        "HEART_RATE": "心率",
        "WEIGHT": "体重",
        "TEMPERATURE": "体温",
        "bp": "血压",
        "bg": "血糖",
        "hr": "心率",
        "weight": "体重",
        "temp": "体温"
    }
    return labels.get(value, value)


def risk_label(risk_level: Optional[str]) -> str:
    return {
        "normal": "正常",
        "warning": "预警",
        "danger": "高危"
    }.get(risk_level or "unknown", "未分级")


def format_measurement_value(item: Measurement) -> str:
    label = measurement_type_label(item.type)
    if item.type == MeasurementType.BLOOD_PRESSURE:
        return f"{int(item.value1)}/{int(item.value2 or 0)} mmHg"
    if item.type == MeasurementType.HEART_RATE:
        return f"{int(item.value1)} bpm"
    if item.type == MeasurementType.BLOOD_SUGAR:
        return f"{round(item.value1, 1)} mmol/L"
    if item.type == MeasurementType.TEMPERATURE:
        return f"{round(item.value1, 1)} ℃"
    if item.type == MeasurementType.WEIGHT:
        return f"{round(item.value1, 1)} kg"
    return f"{label} {round(item.value1, 1)}"


def format_average_value(measurement_type, avg_value1, avg_value2) -> str:
    if measurement_type == MeasurementType.BLOOD_PRESSURE:
        return f"{round(avg_value1 or 0, 1)}/{round(avg_value2 or 0, 1)} mmHg"
    if measurement_type == MeasurementType.HEART_RATE:
        return f"{round(avg_value1 or 0, 1)} bpm"
    if measurement_type == MeasurementType.BLOOD_SUGAR:
        return f"{round(avg_value1 or 0, 1)} mmol/L"
    if measurement_type == MeasurementType.TEMPERATURE:
        return f"{round(avg_value1 or 0, 1)} ℃"
    if measurement_type == MeasurementType.WEIGHT:
        return f"{round(avg_value1 or 0, 1)} kg"
    return str(round(avg_value1 or 0, 1))


@router.get("/situation-awareness")
def get_situation_awareness(
    days: int = Query(30, ge=1, le=365, description="统计最近N天数据"),
    recent_limit: int = Query(12, ge=1, le=50, description="最近异常和最新数据返回条数"),
    db: Session = Depends(get_db)
):
    """管理端态势感知数据"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = now - timedelta(days=days - 1)
    start_day = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    abnormal_levels = ["warning", "danger"]

    total_measurements = db.query(Measurement).count()
    window_query = db.query(Measurement).filter(Measurement.measured_at >= start_day)
    window_measurements = window_query.count()
    today_measurements = db.query(Measurement).filter(Measurement.measured_at >= today_start).count()
    abnormal_measurements = window_query.filter(Measurement.risk_level.in_(abnormal_levels)).count()
    danger_measurements = window_query.filter(Measurement.risk_level == "danger").count()
    total_patients = db.query(PatientProfile).count()
    active_patients = db.query(Measurement.patient_id).filter(
        Measurement.measured_at >= start_day
    ).distinct().count()
    online_devices = db.query(Device).filter(Device.status == "online").count()
    total_devices = db.query(Device).count()
    latest_measurement_at = db.query(func.max(Measurement.measured_at)).scalar()

    risk_rows = window_query.with_entities(
        Measurement.risk_level,
        func.count(Measurement.id)
    ).group_by(Measurement.risk_level).all()
    risk_distribution = [
        {
            "risk_level": row[0] or "unknown",
            "label": risk_label(row[0]),
            "count": row[1]
        }
        for row in risk_rows
    ]

    type_rows = window_query.with_entities(
        Measurement.type,
        func.count(Measurement.id),
        func.avg(Measurement.value1),
        func.avg(Measurement.value2),
        func.sum(case((Measurement.risk_level.in_(abnormal_levels), 1), else_=0))
    ).group_by(Measurement.type).all()
    type_distribution = [
        {
            "type": getattr(row[0], "name", str(row[0])),
            "label": measurement_type_label(row[0]),
            "count": row[1],
            "avg_value": round(row[2] or 0, 2),
            "avg_value2": round(row[3], 2) if row[3] is not None else None,
            "avg_label": format_average_value(row[0], row[2], row[3]),
            "abnormal_count": int(row[4] or 0)
        }
        for row in type_rows
    ]

    trend_rows = db.query(
        func.date(Measurement.measured_at),
        func.count(Measurement.id),
        func.sum(case((Measurement.risk_level.in_(abnormal_levels), 1), else_=0))
    ).filter(
        Measurement.measured_at >= start_day
    ).group_by(
        func.date(Measurement.measured_at)
    ).all()
    trend_map = {row[0]: {"total": row[1], "abnormal": int(row[2] or 0)} for row in trend_rows}
    trend = []
    for index in range(days):
        current_day = start_day + timedelta(days=index)
        key = current_day.date().isoformat()
        values = trend_map.get(key, {"total": 0, "abnormal": 0})
        trend.append({"date": key, **values})

    patient_rows = db.query(
        PatientProfile.id,
        User.name,
        User.phone,
        func.count(Measurement.id).label("measurement_count"),
        func.sum(case((Measurement.risk_level.in_(abnormal_levels), 1), else_=0)).label("abnormal_count"),
        func.max(Measurement.measured_at).label("latest_measurement")
    ).join(
        User, User.id == PatientProfile.user_id
    ).join(
        Measurement, Measurement.patient_id == PatientProfile.id
    ).filter(
        Measurement.measured_at >= start_day
    ).group_by(
        PatientProfile.id,
        User.name,
        User.phone
    ).order_by(
        desc(func.count(Measurement.id))
    ).limit(8).all()
    patient_ranking = [
        {
            "patient_id": row[0],
            "name": row[1],
            "phone": row[2],
            "measurement_count": row[3],
            "abnormal_count": int(row[4] or 0),
            "latest_measurement": row[5].isoformat() if row[5] else None
        }
        for row in patient_rows
    ]

    latest_abnormal_items = db.query(Measurement).options(
        joinedload(Measurement.patient).joinedload(PatientProfile.user)
    ).filter(
        Measurement.risk_level.in_(abnormal_levels)
    ).order_by(
        desc(Measurement.measured_at)
    ).limit(recent_limit).all()

    latest_items = db.query(Measurement).options(
        joinedload(Measurement.patient).joinedload(PatientProfile.user)
    ).order_by(
        desc(Measurement.measured_at)
    ).limit(recent_limit).all()

    def serialize_measurement(item: Measurement):
        patient = item.patient
        user = patient.user if patient else None
        return {
            "id": item.id,
            "patient_id": item.patient_id,
            "patient_name": user.name if user else "未知患者",
            "phone": user.phone if user else "",
            "type": getattr(item.type, "name", str(item.type)),
            "type_label": measurement_type_label(item.type),
            "value": format_measurement_value(item),
            "risk_level": item.risk_level or "unknown",
            "risk_label": risk_label(item.risk_level),
            "ai_suggestion": item.ai_suggestion,
            "measured_at": item.measured_at.isoformat() if item.measured_at else None,
            "device_id": item.device_id
        }

    return {
        "generated_at": now.isoformat(),
        "window_days": days,
        "overview": {
            "total_measurements": total_measurements,
            "window_measurements": window_measurements,
            "today_measurements": today_measurements,
            "abnormal_measurements": abnormal_measurements,
            "danger_measurements": danger_measurements,
            "total_patients": total_patients,
            "active_patients": active_patients,
            "compliance_rate": round((active_patients / total_patients * 100) if total_patients else 0, 1),
            "online_devices": online_devices,
            "total_devices": total_devices,
            "latest_measurement_at": latest_measurement_at.isoformat() if latest_measurement_at else None
        },
        "trend": trend,
        "risk_distribution": risk_distribution,
        "type_distribution": type_distribution,
        "patient_ranking": patient_ranking,
        "latest_abnormal": [serialize_measurement(item) for item in latest_abnormal_items],
        "latest_measurements": [serialize_measurement(item) for item in latest_items]
    }


@router.get("/institutions/{institution_id}/kpi", response_model=KPIStats)
def get_institution_kpi(institution_id: int, db: Session = Depends(get_db)):
    """获取机构考核指标"""
    # 管理患者数
    managed_patients = db.query(PatientProfile).count()
    
    # 异常患者数（最近7天有warning或danger风险的患者）
    abnormal_patient_ids = db.query(Measurement.patient_id).filter(
        Measurement.measured_at >= datetime.now() - timedelta(days=7),
        or_(Measurement.risk_level == "warning", Measurement.risk_level == "danger")
    ).distinct().all()
    abnormal_patients = len(abnormal_patient_ids)
    
    # 随访完成率
    total_followups = db.query(FollowUp).filter(
        FollowUp.scheduled_date <= datetime.now()
    ).count()
    completed_followups = db.query(FollowUp).filter(
        FollowUp.scheduled_date <= datetime.now(),
        FollowUp.completed == True
    ).count()
    followup_completion_rate = (completed_followups / total_followups * 100) if total_followups > 0 else 0.0
    
    # 监测依从率（最近7天有监测的患者占比）
    patients_with_recent_measurements = db.query(Measurement.patient_id).filter(
        Measurement.measured_at >= datetime.now() - timedelta(days=7)
    ).distinct().count()
    measurement_compliance_rate = (patients_with_recent_measurements / managed_patients * 100) if managed_patients > 0 else 0.0
    
    # 慢性病控制率（正常数据占比）
    total_recent_measurements = db.query(Measurement).filter(
        Measurement.measured_at >= datetime.now() - timedelta(days=30)
    ).count()
    normal_measurements = db.query(Measurement).filter(
        Measurement.measured_at >= datetime.now() - timedelta(days=30),
        Measurement.risk_level == "normal"
    ).count()
    chronic_disease_control_rate = (normal_measurements / total_recent_measurements * 100) if total_recent_measurements > 0 else 0.0
    
    return KPIStats(
        institution_id=institution_id,
        managed_patients=managed_patients,
        abnormal_patients=abnormal_patients,
        followup_completion_rate=round(followup_completion_rate, 2),
        measurement_compliance_rate=round(measurement_compliance_rate, 2),
        chronic_disease_control_rate=round(chronic_disease_control_rate, 2)
    )


@router.get("/kpi", response_model=KPIStats)
def get_default_kpi(db: Session = Depends(get_db)):
    """获取默认机构考核指标"""
    return get_institution_kpi(1, db)


# ============= 用户管理相关 =============

@router.get("/users", response_model=List[UserOut])
def list_users(
    role: Optional[UserRole] = None,
    search: Optional[str] = None,
    status: Optional[bool] = None,
    limit: int = Query(50, description="返回数据条数限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if status is not None:
        query = query.filter(User.status == status)
    
    if search:
        query = query.filter(
            or_(
                User.name.like(f"%{search}%"),
                User.phone.like(f"%{search}%")
            )
        )
    
    users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    return users


@router.get("/users-page")
def list_users_page(
    role: Optional[UserRole] = None,
    search: Optional[str] = None,
    status: Optional[bool] = None,
    limit: int = Query(20, ge=1, le=100, description="每页数据条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status is not None:
        query = query.filter(User.status == status)
    if search:
        query = query.filter(
            or_(
                User.name.like(f"%{search}%"),
                User.phone.like(f"%{search}%")
            )
        )
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    return {
        "items": [UserOut.model_validate(user) for user in users],
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": offset // limit + 1,
        "total_pages": max(1, (total + limit - 1) // limit)
    }


@router.get("/users/{user_id}", response_model=UserOut)
def get_user_detail(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/users", response_model=UserOut)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    """创建用户"""
    # 检查手机号是否已存在
    existing_user = db.query(User).filter(User.phone == body.phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="手机号已存在")
    
    # 创建用户
    user = User(
        phone=body.phone,
        name=body.name,
        avatar=body.avatar,
        role=body.role,
        password=hash_password(body.password) if body.password else hash_password("123456")
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 根据角色创建对应的档案
    if user.role == UserRole.PATIENT:
        profile = PatientProfile(user_id=user.id)
        db.add(profile)
    elif user.role == UserRole.DOCTOR:
        profile = DoctorProfile(user_id=user.id)
        db.add(profile)
    elif user.role == UserRole.ADMIN:
        profile = AdminProfile(user_id=user.id)
        db.add(profile)
    
    db.commit()
    
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: AdminUserUpdate, db: Session = Depends(get_db)):
    """更新用户：管理员可改姓名、手机号、头像、密码、启用状态"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if body.name is not None:
        user.name = body.name
    if body.phone is not None and body.phone != user.phone:
        if db.query(User).filter(User.phone == body.phone, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="手机号已被占用")
        user.phone = body.phone
    if body.avatar is not None:
        user.avatar = body.avatar
    if body.password:
        user.password = hash_password(body.password)
    if body.status is not None:
        user.status = body.status

    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户：同时清理三类角色档案，避免孤儿档案"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 清理对应的角色档案
    db.query(PatientProfile).filter(PatientProfile.user_id == user_id).delete()
    db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).delete()
    db.query(AdminProfile).filter(AdminProfile.user_id == user_id).delete()

    db.delete(user)
    db.commit()

    return {"message": "用户删除成功"}


@router.put("/users/{user_id}/status")
def update_user_status(user_id: int, body: UserStatusUpdate, db: Session = Depends(get_db)):
    """更新用户状态（启用/禁用）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    status = body.status if body.status is not None else body.is_active
    if status is None:
        raise HTTPException(status_code=400, detail="缺少用户状态")
    
    user.status = status
    user.updated_at = datetime.now()
    db.commit()
    
    return {"message": f"用户已{'启用' if status else '禁用'}"}


# ============= 设备管理相关 =============

@router.get("/devices", response_model=List[DeviceOut])
def list_devices(
    status: Optional[str] = None,
    limit: int = Query(50, description="返回数据条数限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取设备列表"""
    query = db.query(Device)
    
    if status:
        query = query.filter(Device.status == status)
    
    devices = query.order_by(desc(Device.created_at)).offset(offset).limit(limit).all()
    return devices


@router.get("/devices/{device_id}", response_model=DeviceOut)
def get_device_detail(device_id: int, db: Session = Depends(get_db)):
    """获取设备详情"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.post("/devices", response_model=DeviceOut)
def create_device(body: DeviceCreate, db: Session = Depends(get_db)):
    """创建设备"""
    # 检查设备ID是否已存在
    existing_device = db.query(Device).filter(Device.device_id == body.device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="设备ID已存在")
    
    device = Device(**body.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return device


@router.put("/devices/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, body: DeviceUpdate, db: Session = Depends(get_db)):
    """更新设备"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(device, key, value)
    
    device.updated_at = datetime.now()
    db.commit()
    db.refresh(device)
    
    return device


@router.delete("/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """删除设备"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    db.delete(device)
    db.commit()
    
    return {"message": "设备删除成功"}


# ============= 新闻管理相关 =============

@router.get("/news", response_model=List[NewsOut])
def list_all_news(
    published: Optional[bool] = None,
    limit: int = Query(50, description="返回数据条数限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取新闻列表"""
    query = db.query(News)
    
    if published is not None:
        query = query.filter(News.published == published)
    
    news_list = query.order_by(desc(News.created_at)).offset(offset).limit(limit).all()
    return news_list


@router.post("/news", response_model=NewsOut)
def create_news(body: NewsCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """创建新闻"""
    author_id = get_current_user_id(authorization)
    news = News(
        title=body.title,
        content=body.content,
        category=body.category,
        author_id=author_id
    )
    
    db.add(news)
    db.commit()
    db.refresh(news)
    
    return news


@router.put("/news/{news_id}", response_model=NewsOut)
def update_news(news_id: int, body: NewsUpdate, db: Session = Depends(get_db)):
    """更新新闻"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(news, key, value)
    
    # 如果发布状态改变，更新发布时间
    if body.published and not news.published:
        news.published_at = datetime.now()
    
    news.updated_at = datetime.now()
    db.commit()
    db.refresh(news)
    
    return news


@router.delete("/news/{news_id}")
def delete_news(news_id: int, db: Session = Depends(get_db)):
    """删除新闻"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    
    db.delete(news)
    db.commit()
    
    return {"message": "新闻删除成功"}


# ============= 系统日志相关 =============

@router.post("/logs")
def create_system_log(
    user_id: int,
    action: str,
    module: Optional[str] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建系统日志"""
    log = SystemLog(
        user_id=user_id,
        action=action,
        module=module,
        description=description,
        ip_address=ip_address
    )
    
    db.add(log)
    db.commit()
    
    return {"message": "日志记录成功"}


@router.get("/logs")
def list_system_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    days: int = Query(7, description="查询最近N天的日志"),
    limit: int = Query(100, description="返回数据条数限制"),
    db: Session = Depends(get_db)
):
    """获取系统日志列表"""
    query = db.query(SystemLog).filter(
        SystemLog.created_at >= datetime.now() - timedelta(days=days)
    )
    
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    if action:
        query = query.filter(SystemLog.action == action)
    
    logs = query.order_by(desc(SystemLog.created_at)).limit(limit).all()
    return logs


@router.get("/operations")
def get_operation_data(days: int = Query(7, description="查询最近N天的数据"), db: Session = Depends(get_db)):
    """获取运营数据"""
    start_time = datetime.now() - timedelta(days=days)
    return {
        "days": days,
        "new_users": db.query(User).filter(User.created_at >= start_time).count(),
        "active_users": db.query(User).filter(User.last_login >= start_time).count(),
        "new_measurements": db.query(Measurement).filter(Measurement.created_at >= start_time).count(),
        "online_devices": db.query(Device).filter(Device.status == "online").count(),
        "total_devices": db.query(Device).count()
    }


@router.get("/compliance")
def get_compliance_data(days: int = Query(30, description="查询最近N天的数据"), db: Session = Depends(get_db)):
    """获取合规检查数据"""
    start_time = datetime.now() - timedelta(days=days)
    total_users = db.query(User).count()
    disabled_users = db.query(User).filter(User.status == False).count()
    total_logs = db.query(SystemLog).filter(SystemLog.created_at >= start_time).count()
    abnormal_measurements = db.query(Measurement).filter(
        Measurement.measured_at >= start_time,
        or_(Measurement.risk_level == "warning", Measurement.risk_level == "danger")
    ).count()
    return {
        "days": days,
        "total_users": total_users,
        "disabled_users": disabled_users,
        "recent_system_logs": total_logs,
        "abnormal_measurements": abnormal_measurements
    }


# ============= 商品管理（管理端） =============

@router.get("/products", response_model=List[ShopProductOut])
def admin_list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[bool] = None,
    is_prescription: Optional[bool] = None,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """商城商品列表（含上下架商品）"""
    query = db.query(ShopProduct)
    if search:
        query = query.filter(ShopProduct.name.like(f"%{search}%"))
    if category:
        query = query.filter(ShopProduct.category == category)
    if status is not None:
        query = query.filter(ShopProduct.status == status)
    if is_prescription is not None:
        query = query.filter(ShopProduct.is_prescription == is_prescription)
    return query.order_by(desc(ShopProduct.created_at)).offset(offset).limit(limit).all()


@router.get("/products/{product_id}", response_model=ShopProductOut)
def admin_get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ShopProduct).filter(ShopProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product


@router.post("/products", response_model=ShopProductOut)
def admin_create_product(body: ProductCreate, db: Session = Depends(get_db)):
    """创建商品"""
    if body.price < 0:
        raise HTTPException(status_code=400, detail="价格不能为负数")
    if body.stock < 0:
        raise HTTPException(status_code=400, detail="库存不能为负数")
    product = ShopProduct(**body.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ShopProductOut)
def admin_update_product(product_id: int, body: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(ShopProduct).filter(ShopProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    data = body.model_dump(exclude_unset=True)
    if "price" in data and data["price"] is not None and data["price"] < 0:
        raise HTTPException(status_code=400, detail="价格不能为负数")
    if "stock" in data and data["stock"] is not None and data["stock"] < 0:
        raise HTTPException(status_code=400, detail="库存不能为负数")
    for key, value in data.items():
        setattr(product, key, value)
    product.updated_at = datetime.now()
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def admin_delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除商品（软删除：下架）。若已有订单关联，仅下架不物理删除。"""
    product = db.query(ShopProduct).filter(ShopProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    has_orders = db.query(ShopOrderItem).filter(ShopOrderItem.product_id == product_id).first() is not None
    if has_orders:
        product.status = False
        product.updated_at = datetime.now()
        db.commit()
        return {"message": "商品已下架（存在历史订单，未做物理删除）"}
    db.delete(product)
    db.commit()
    return {"message": "商品已删除"}


# ============= 订单管理（管理端） =============

@router.get("/orders", response_model=List[ShopOrderOut])
def admin_list_orders(
    status: Optional[str] = None,
    patient_id: Optional[int] = None,
    days: Optional[int] = Query(None, description="只查询最近 N 天，缺省返回全部"),
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    query = db.query(ShopOrder)
    if status:
        query = query.filter(ShopOrder.status == status)
    if patient_id:
        query = query.filter(ShopOrder.patient_id == patient_id)
    if days:
        query = query.filter(ShopOrder.created_at >= datetime.now() - timedelta(days=days))
    return query.order_by(desc(ShopOrder.created_at)).offset(offset).limit(limit).all()


@router.get("/orders/{order_id}", response_model=ShopOrderOut)
def admin_get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(ShopOrder).filter(ShopOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.put("/orders/{order_id}/ship", response_model=ShopOrderOut)
def admin_ship_order(order_id: int, body: ShopOrderShip, db: Session = Depends(get_db)):
    """订单发货"""
    order = db.query(ShopOrder).filter(ShopOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "paid":
        raise HTTPException(status_code=400, detail="只有已支付订单可以发货")
    order.status = "shipped"
    order.shipped_at = datetime.now()
    order.updated_at = datetime.now()
    if body.note:
        order.remark = (order.remark or "") + f"\n[发货备注] {body.note}"
    db.commit()
    db.refresh(order)
    return order


@router.put("/orders/{order_id}/cancel", response_model=ShopOrderOut)
def admin_cancel_order(order_id: int, db: Session = Depends(get_db)):
    """管理员取消订单（恢复库存）"""
    order = db.query(ShopOrder).filter(ShopOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="当前状态不允许取消")
    for item in order.items:
        if item.product:
            item.product.stock += item.quantity
            item.product.sales_count = max(0, item.product.sales_count - item.quantity)
    order.status = "cancelled"
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


# ============= 处方管理（管理端） =============

def _admin_build_prescription(prescription: Prescription) -> dict:
    doctor = prescription.doctor
    doctor_user = doctor.user if doctor else None
    return {
        "id": prescription.id,
        "patient_id": prescription.patient_id,
        "status": prescription.status,
        "diagnosis": prescription.diagnosis,
        "notes": prescription.notes,
        "valid_until": prescription.valid_until,
        "created_at": prescription.created_at,
        "doctor": {
            "id": doctor.id if doctor else 0,
            "user_id": doctor.user_id if doctor else 0,
            "name": doctor_user.name if doctor_user else "",
            "avatar": doctor_user.avatar if doctor_user else None,
            "title": doctor.title if doctor else None,
            "department": doctor.department if doctor else None
        },
        "items": prescription.items
    }


@router.get("/prescriptions", response_model=List[PrescriptionOut])
def admin_list_prescriptions(
    status: Optional[str] = None,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    query = db.query(Prescription)
    if status:
        query = query.filter(Prescription.status == status)
    if doctor_id:
        query = query.filter(Prescription.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Prescription.patient_id == patient_id)
    items = query.order_by(desc(Prescription.created_at)).offset(offset).limit(limit).all()
    return [_admin_build_prescription(item) for item in items]


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionOut)
def admin_get_prescription(prescription_id: int, db: Session = Depends(get_db)):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="处方不存在")
    return _admin_build_prescription(prescription)


@router.put("/prescriptions/{prescription_id}", response_model=PrescriptionOut)
def admin_update_prescription(prescription_id: int, body: PrescriptionUpdate, db: Session = Depends(get_db)):
    """管理员审核处方（修改状态、诊断、备注、有效期）"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="处方不存在")
    data = body.model_dump(exclude_unset=True)
    items = data.pop("items", None)
    for key, value in data.items():
        setattr(prescription, key, value)
    if items is not None:
        product_ids = [item["product_id"] for item in items]
        products = db.query(ShopProduct).filter(ShopProduct.id.in_(product_ids), ShopProduct.status == True).all()
        product_map = {product.id: product for product in products}
        for item in items:
            if item["product_id"] not in product_map:
                raise HTTPException(status_code=404, detail=f"药品 {item['product_id']} 不存在或已下架")
        db.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == prescription.id).delete()
        for item in items:
            db.add(PrescriptionItem(prescription_id=prescription.id, **item))
    prescription.updated_at = datetime.now()
    db.commit()
    db.refresh(prescription)
    return _admin_build_prescription(prescription)


# ============= 患者档案管理（管理端） =============

def _build_admin_patient_detail(db: Session, patient: PatientProfile) -> PatientDetail:
    total_measurements = db.query(Measurement).filter(Measurement.patient_id == patient.id).count()
    latest = db.query(Measurement).filter(
        Measurement.patient_id == patient.id
    ).order_by(desc(Measurement.measured_at)).first()
    return PatientDetail(
        id=patient.id,
        user=patient.user,
        profile=patient,
        total_measurements=total_measurements,
        latest_measurement=latest.measured_at if latest else None
    )


@router.get("/patients", response_model=List[PatientDetail])
def admin_list_patients(
    search: Optional[str] = None,
    doctor_id: Optional[int] = None,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    query = db.query(PatientProfile).options(joinedload(PatientProfile.user))
    if doctor_id:
        query = query.filter(PatientProfile.doctor_id == doctor_id)
    if search:
        query = query.join(User).filter(or_(User.name.like(f"%{search}%"), User.phone.like(f"%{search}%")))
    patients = query.offset(offset).limit(limit).all()
    return [_build_admin_patient_detail(db, p) for p in patients]


@router.get("/patients/{patient_id}", response_model=PatientDetail)
def admin_get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    return _build_admin_patient_detail(db, patient)


@router.put("/patients/{patient_id}", response_model=PatientDetail)
def admin_update_patient(patient_id: int, body: AdminPatientUpdate, db: Session = Depends(get_db)):
    """管理员更新患者档案与用户基础信息"""
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    user = db.query(User).filter(User.id == patient.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    data = body.model_dump(exclude_unset=True)
    # 用户基础字段
    if "name" in data:
        user.name = data["name"]
    if "avatar" in data:
        user.avatar = data["avatar"]
    if "phone" in data and data["phone"] and data["phone"] != user.phone:
        if db.query(User).filter(User.phone == data["phone"], User.id != user.id).first():
            raise HTTPException(status_code=400, detail="手机号已被占用")
        user.phone = data["phone"]
    # 档案字段
    profile_fields = {"age", "gender", "address", "emergency_contact", "emergency_phone",
                      "height", "weight", "chronic_diseases", "allergies", "doctor_id"}
    for key in profile_fields:
        if key in data:
            setattr(patient, key, data[key])
    user.updated_at = datetime.now()
    patient.updated_at = datetime.now()
    db.commit()
    db.refresh(patient)
    return _build_admin_patient_detail(db, patient)


# ============= 医生档案管理（管理端） =============

def _build_admin_doctor_detail(db: Session, doctor: DoctorProfile) -> DoctorDetail:
    patient_count = db.query(PatientProfile).filter(PatientProfile.doctor_id == doctor.id).count()
    return DoctorDetail(
        id=doctor.id,
        user_id=doctor.user_id,
        user=doctor.user,
        profile=doctor,
        name=doctor.user.name if doctor.user else "",
        avatar=doctor.user.avatar if doctor.user else None,
        title=doctor.title,
        department=doctor.department,
        hospital=doctor.hospital,
        specialty=doctor.introduction,
        introduction=doctor.introduction,
        patient_count=patient_count,
        consultation_count=0
    )


@router.get("/doctors", response_model=List[DoctorDetail])
def admin_list_doctors(
    search: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    query = db.query(DoctorProfile).options(joinedload(DoctorProfile.user)).join(User)
    if department:
        query = query.filter(DoctorProfile.department == department)
    if search:
        query = query.filter(or_(User.name.like(f"%{search}%"), User.phone.like(f"%{search}%")))
    doctors = query.offset(offset).limit(limit).all()
    return [_build_admin_doctor_detail(db, d) for d in doctors]


@router.get("/doctors/{doctor_id}", response_model=DoctorDetail)
def admin_get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    return _build_admin_doctor_detail(db, doctor)


@router.put("/doctors/{doctor_id}", response_model=DoctorDetail)
def admin_update_doctor(doctor_id: int, body: AdminDoctorUpdate, db: Session = Depends(get_db)):
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    user = db.query(User).filter(User.id == doctor.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    data = body.model_dump(exclude_unset=True)
    if "name" in data:
        user.name = data["name"]
    if "avatar" in data:
        user.avatar = data["avatar"]
    if "phone" in data and data["phone"] and data["phone"] != user.phone:
        if db.query(User).filter(User.phone == data["phone"], User.id != user.id).first():
            raise HTTPException(status_code=400, detail="手机号已被占用")
        user.phone = data["phone"]
    if "user_status" in data:
        user.status = data["user_status"]
    profile_fields = {"department", "title", "license_number", "hospital", "introduction"}
    for key in profile_fields:
        if key in data:
            setattr(doctor, key, data[key])
    user.updated_at = datetime.now()
    doctor.updated_at = datetime.now()
    db.commit()
    db.refresh(doctor)
    return _build_admin_doctor_detail(db, doctor)
