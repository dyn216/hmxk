"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class MeasurementType(str, enum.Enum):
    """监测类型枚举"""
    BLOOD_PRESSURE = "bp"  # 血压
    BLOOD_SUGAR = "bg"  # 血糖
    HEART_RATE = "hr"  # 心率
    WEIGHT = "weight"  # 体重
    TEMPERATURE = "temp"  # 体温


class User(Base):
    """用户基础表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password = Column(String(128))  # 密码哈希
    name = Column(String(50), nullable=False)
    avatar = Column(String(255))
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Boolean, default=True)  # 账号状态
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime)
    
    # 关联关系
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False)
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False)
    admin_profile = relationship("AdminProfile", back_populates="user", uselist=False)


class PatientProfile(Base):
    """患者档案表"""
    __tablename__ = "patient_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    age = Column(Integer)
    gender = Column(String(10))
    id_card = Column(String(18))
    address = Column(String(255))
    emergency_contact = Column(String(50))
    emergency_phone = Column(String(20))
    
    # 健康信息
    height = Column(Float)  # 身高 cm
    weight = Column(Float)  # 体重 kg
    chronic_diseases = Column(Text)  # 慢性病史（JSON格式）
    allergies = Column(Text)  # 过敏史
    
    # 签约医生
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"))
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    user = relationship("User", back_populates="patient_profile")
    doctor = relationship("DoctorProfile", foreign_keys=[doctor_id])
    measurements = relationship("Measurement", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    guardians = relationship("Guardian", back_populates="patient")


class DoctorProfile(Base):
    """医生档案表"""
    __tablename__ = "doctor_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    department = Column(String(50))  # 科室
    title = Column(String(50))  # 职称
    license_number = Column(String(50))  # 执业证号
    hospital = Column(String(100))  # 所属医院/机构
    introduction = Column(Text)  # 简介
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    user = relationship("User", back_populates="doctor_profile")
    messages = relationship("Message", back_populates="doctor")
    consultations = relationship("Consultation", back_populates="doctor")


class AdminProfile(Base):
    """管理员档案表"""
    __tablename__ = "admin_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    institution = Column(String(100))  # 所属机构
    permissions = Column(Text)  # 权限配置（JSON格式）
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    user = relationship("User", back_populates="admin_profile")


class Measurement(Base):
    """监测数据表"""
    __tablename__ = "measurements"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    type = Column(Enum(MeasurementType), nullable=False)
    
    # 监测值（根据类型使用不同字段）
    value1 = Column(Float, nullable=False)  # 血压：收缩压；血糖：数值；心率：数值
    value2 = Column(Float)  # 血压：舒张压
    
    measured_at = Column(DateTime, nullable=False)
    device_id = Column(String(50))  # 设备ID
    notes = Column(Text)  # 备注
    
    # AI分析结果
    risk_level = Column(String(20))  # 风险等级：normal, warning, danger
    ai_suggestion = Column(Text)  # AI建议
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    patient = relationship("PatientProfile", back_populates="measurements")


class Medication(Base):
    """用药管理表"""
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    
    drug_name = Column(String(100), nullable=False)
    dosage = Column(String(50))  # 剂量
    frequency = Column(String(50))  # 频率
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # 提醒设置
    reminder_times = Column(Text)  # 提醒时间（JSON数组）
    reminder_enabled = Column(Boolean, default=True)
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    patient = relationship("PatientProfile", back_populates="medications")


class PatientAddress(Base):
    __tablename__ = "patient_addresses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ShopProduct(Base):
    __tablename__ = "shop_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specification = Column(String(100))
    price = Column(Float, nullable=False)
    image_url = Column(String(255))
    category = Column(String(50))
    manufacturer = Column(String(100))
    approval_number = Column(String(100))
    description = Column(Text)
    usage = Column(Text)
    precautions = Column(Text)
    unit = Column(String(20), default="盒")
    stock = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)
    is_prescription = Column(Boolean, default=False)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ShopCartItem(Base):
    __tablename__ = "shop_cart_items"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("shop_products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    product = relationship("ShopProduct")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    consultation_id = Column(Integer, ForeignKey("consultations.id"))
    status = Column(String(20), default="approved")
    diagnosis = Column(Text)
    notes = Column(Text)
    valid_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    doctor = relationship("DoctorProfile")
    items = relationship("PrescriptionItem", back_populates="prescription")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("shop_products.id"))
    dosage = Column(String(100))
    frequency = Column(String(100))
    duration = Column(String(100))

    prescription = relationship("Prescription", back_populates="items")
    product = relationship("ShopProduct")


class ShopOrder(Base):
    __tablename__ = "shop_orders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="pending")
    total_amount = Column(Float, nullable=False)
    receiver_name = Column(String(50), nullable=False)
    receiver_phone = Column(String(20), nullable=False)
    receiver_address = Column(String(255), nullable=False)
    remark = Column(Text)
    paid_at = Column(DateTime)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    items = relationship("ShopOrderItem", back_populates="order")


class ShopOrderItem(Base):
    __tablename__ = "shop_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("shop_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("shop_products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("ShopOrder", back_populates="items")
    product = relationship("ShopProduct")


class Guardian(Base):
    """监护人表"""
    __tablename__ = "guardians"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    relation_type = Column(String(20))

    @property
    def relation(self):
        return self.relation_type
    
    can_view_data = Column(Boolean, default=True)
    can_receive_alerts = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    patient = relationship("PatientProfile", back_populates="guardians")

    @property
    def relationship(self):
        return self.relation_type


class Device(Base):
    """设备管理表"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), unique=True, nullable=False)
    device_name = Column(String(100))
    device_type = Column(String(50))  # 设备类型：血压计、血糖仪等
    model = Column(String(50))  # 型号
    
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"))
    
    status = Column(String(20))  # 状态：online, offline, error
    battery_level = Column(Integer)  # 电量百分比
    last_sync = Column(DateTime)  # 最后同步时间
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    
    content = Column(Text, nullable=False)
    message_type = Column(String(20))  # text, image, voice
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    # 如果是医生发送的消息
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"))
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    doctor = relationship("DoctorProfile", back_populates="messages")


class Consultation(Base):
    """视频问诊记录表"""
    __tablename__ = "consultations"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"))
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"))
    
    scheduled_time = Column(DateTime)  # 预约时间
    start_time = Column(DateTime)  # 开始时间
    end_time = Column(DateTime)  # 结束时间
    
    status = Column(String(20))  # pending, ongoing, completed, cancelled
    
    # 问诊记录
    chief_complaint = Column(Text)  # 主诉
    diagnosis = Column(Text)  # 诊断
    treatment_plan = Column(Text)  # 治疗方案
    prescription = Column(Text)  # 处方（JSON格式）
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    doctor = relationship("DoctorProfile", back_populates="consultations")


class FollowUp(Base):
    """随访计划表"""
    __tablename__ = "follow_ups"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"))
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"))
    
    scheduled_date = Column(DateTime, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    follow_up_type = Column(String(20))  # phone, video, in_person
    notes = Column(Text)
    result = Column(Text)  # 随访结果
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class News(Base):
    """新闻动态表"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    category = Column(String(50))  # 分类：公告、指南、通知
    
    author_id = Column(Integer, ForeignKey("users.id"))
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    module = Column(String(50))
    description = Column(Text)
    ip_address = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.now)
