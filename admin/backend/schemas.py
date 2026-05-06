"""
Pydantic模型定义，用于API请求和响应验证
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models import UserRole, MeasurementType


# ============= 通用模型 =============

class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., description="手机号")
    password: Optional[str] = Field(None, description="密码（可选，简化版可用手机号直接登录）")


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user_id: int
    role: UserRole
    name: str
    avatar: Optional[str] = None


class MessageModel(BaseModel):
    """通用消息响应"""
    message: str
    code: int = 200


# ============= 用户相关 =============

class UserBase(BaseModel):
    """用户基础信息"""
    phone: str
    name: str
    avatar: Optional[str] = None
    role: UserRole


class UserCreate(UserBase):
    """创建用户"""
    password: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用户"""
    name: Optional[str] = None
    avatar: Optional[str] = None
    password: Optional[str] = None


class UserOut(UserBase):
    """用户输出"""
    id: int
    status: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============= 患者相关 =============

class PatientProfileBase(BaseModel):
    """患者档案基础信息"""
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    chronic_diseases: Optional[str] = None
    allergies: Optional[str] = None


class PatientProfileUpdate(PatientProfileBase):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None


class PatientProfileCreate(PatientProfileBase):
    """创建患者档案"""
    user_id: int


class PatientProfileOut(PatientProfileBase):
    """患者档案输出"""
    id: int
    user_id: int
    doctor_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PatientDetail(BaseModel):
    """患者详细信息（包含用户信息）"""
    id: int
    user: UserOut
    profile: PatientProfileOut
    total_measurements: int = 0
    latest_measurement: Optional[datetime] = None


# ============= 医生相关 =============

class DoctorProfileBase(BaseModel):
    """医生档案基础信息"""
    department: Optional[str] = None
    title: Optional[str] = None
    license_number: Optional[str] = None
    hospital: Optional[str] = None
    introduction: Optional[str] = None


class DoctorProfileCreate(DoctorProfileBase):
    """创建医生档案"""
    user_id: int


class DoctorProfileOut(DoctorProfileBase):
    """医生档案输出"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DoctorDetail(BaseModel):
    """医生详细信息"""
    id: int
    user_id: Optional[int] = None
    user: UserOut
    profile: DoctorProfileOut
    name: Optional[str] = None
    avatar: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    hospital: Optional[str] = None
    specialty: Optional[str] = None
    introduction: Optional[str] = None
    patient_count: int = 0
    consultation_count: int = 0


# ============= 监测数据相关 =============

class MeasurementCreate(BaseModel):
    """创建监测数据"""
    type: MeasurementType
    value1: float
    value2: Optional[float] = None
    measured_at: datetime
    device_id: Optional[str] = None
    notes: Optional[str] = None


class MeasurementOut(BaseModel):
    """监测数据输出"""
    id: int
    patient_id: int
    type: MeasurementType
    value1: float
    value2: Optional[float] = None
    measured_at: datetime
    device_id: Optional[str] = None
    notes: Optional[str] = None
    risk_level: Optional[str] = None
    ai_suggestion: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MeasurementStats(BaseModel):
    """监测数据统计"""
    total_count: int
    avg_value: Optional[float] = None
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    latest_measurement: Optional[MeasurementOut] = None


# ============= 用药管理相关 =============

class MedicationCreate(BaseModel):
    """创建用药记录"""
    drug_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    reminder_times: Optional[str] = None
    reminder_enabled: bool = True
    notes: Optional[str] = None


class MedicationUpdate(BaseModel):
    """更新用药记录"""
    drug_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    end_date: Optional[datetime] = None
    reminder_times: Optional[str] = None
    reminder_enabled: Optional[bool] = None
    notes: Optional[str] = None


class MedicationOut(BaseModel):
    """用药记录输出"""
    id: int
    patient_id: int
    drug_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    reminder_times: Optional[str] = None
    reminder_enabled: bool
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 监护人相关 =============

class GuardianCreate(BaseModel):
    """创建监护人"""
    name: str
    phone: str
    relationship: Optional[str] = None
    can_view_data: bool = True
    can_receive_alerts: bool = True


class GuardianOut(BaseModel):
    """监护人输出"""
    id: int
    patient_id: int
    name: str
    phone: str
    relation: Optional[str] = None
    relationship: Optional[str] = None
    relation_type: Optional[str] = None
    can_view_data: bool
    can_receive_alerts: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 设备相关 =============

class DeviceCreate(BaseModel):
    """创建设备"""
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None


class DeviceUpdate(BaseModel):
    """更新设备"""
    device_name: Optional[str] = None
    status: Optional[str] = None
    battery_level: Optional[int] = None


class DeviceOut(BaseModel):
    """设备输出"""
    id: int
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    patient_id: Optional[int] = None
    status: Optional[str] = None
    battery_level: Optional[int] = None
    last_sync: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PatientAddressCreate(BaseModel):
    name: str
    phone: str
    address: str
    is_default: bool = False


class PatientAddressUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_default: Optional[bool] = None


class PatientAddressOut(PatientAddressCreate):
    id: int
    patient_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ShopProductOut(BaseModel):
    id: int
    name: str
    specification: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    approval_number: Optional[str] = None
    description: Optional[str] = None
    usage: Optional[str] = None
    precautions: Optional[str] = None
    unit: Optional[str] = None
    stock: int = 0
    sales_count: int = 0
    is_prescription: bool = False
    status: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class ShopCartCreate(BaseModel):
    product_id: int
    quantity: int = 1


class ShopCartUpdate(BaseModel):
    quantity: int


class ShopCartItemOut(BaseModel):
    id: int
    patient_id: int
    product_id: int
    quantity: int
    product: ShopProductOut
    created_at: datetime

    class Config:
        from_attributes = True


class ShopOrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    price: Optional[float] = None


class ShopOrderCreate(BaseModel):
    items: List[ShopOrderItemCreate]
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    remark: Optional[str] = None
    prescription_id: Optional[int] = None


class ShopOrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product: ShopProductOut

    class Config:
        from_attributes = True


class ShopOrderOut(BaseModel):
    id: int
    patient_id: int
    prescription_id: Optional[int] = None
    order_number: str
    status: str
    total_amount: float
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    remark: Optional[str] = None
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    items: List[ShopOrderItemOut] = []

    class Config:
        from_attributes = True


class PrescriptionProductOut(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    specification: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None

    class Config:
        from_attributes = True


class PrescriptionItemOut(BaseModel):
    id: int
    product: Optional[PrescriptionProductOut] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None

    class Config:
        from_attributes = True


class PrescriptionDoctorOut(BaseModel):
    id: int
    user_id: int
    name: str
    avatar: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None


class PrescriptionOut(BaseModel):
    id: int
    patient_id: int
    status: str
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    valid_until: Optional[datetime] = None
    created_at: datetime
    doctor: PrescriptionDoctorOut
    items: List[PrescriptionItemOut] = []


# ============= 消息相关 =============

class MessageCreate(BaseModel):
    """创建消息"""
    receiver_id: Optional[int] = None
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    content: str
    message_type: str = "text"


class MessageOut(BaseModel):
    """消息输出"""
    id: int
    sender_id: int
    receiver_id: int
    content: str
    message_type: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 问诊相关 =============

class ConsultationCreate(BaseModel):
    """创建问诊"""
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    scheduled_time: datetime
    chief_complaint: Optional[str] = None


class ConsultationUpdate(BaseModel):
    """更新问诊"""
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None


class ConsultationOut(BaseModel):
    """问诊输出"""
    id: int
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 随访相关 =============

class FollowUpCreate(BaseModel):
    """创建随访"""
    patient_id: int
    doctor_id: Optional[int] = None
    scheduled_date: datetime
    follow_up_type: str = "phone"
    notes: Optional[str] = None


class UserStatusUpdate(BaseModel):
    """更新用户状态"""
    is_active: Optional[bool] = None
    status: Optional[bool] = None


class FollowUpUpdate(BaseModel):
    """更新随访"""
    completed: bool
    result: Optional[str] = None


class FollowUpOut(BaseModel):
    """随访输出"""
    id: int
    patient_id: int
    doctor_id: int
    scheduled_date: datetime
    completed: bool
    completed_at: Optional[datetime] = None
    follow_up_type: str
    notes: Optional[str] = None
    result: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 新闻动态相关 =============

class NewsCreate(BaseModel):
    """创建新闻"""
    title: str
    content: Optional[str] = None
    category: Optional[str] = None


class NewsUpdate(BaseModel):
    """更新新闻"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    published: Optional[bool] = None


class NewsOut(BaseModel):
    """新闻输出"""
    id: int
    title: str
    content: Optional[str] = None
    category: Optional[str] = None
    published: bool
    published_at: Optional[datetime] = None
    views: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 统计数据相关 =============

class DashboardStats(BaseModel):
    """管理后台统计数据"""
    total_users: int = 0
    total_patients: int = 0
    total_doctors: int = 0
    total_measurements: int = 0
    active_users_today: int = 0
    new_users_today: int = 0
    online_devices: int = 0
    total_devices: int = 0


class KPIStats(BaseModel):
    """机构考核指标"""
    institution_id: int
    managed_patients: int = 0
    abnormal_patients: int = 0
    followup_completion_rate: float = 0.0
    measurement_compliance_rate: float = 0.0
    chronic_disease_control_rate: float = 0.0


# ============= 账号安全相关 =============

class RegisterRequest(BaseModel):
    """患者注册请求"""
    phone: str
    password: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None


class PasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


class PhoneChange(BaseModel):
    """修改手机号请求"""
    new_phone: str
    password: str


# ============= 文件上传 =============

class UploadResponse(BaseModel):
    url: str
    filename: str
    size: int


# ============= 商品管理（管理端） =============

class ProductCreate(BaseModel):
    name: str
    specification: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    approval_number: Optional[str] = None
    description: Optional[str] = None
    usage: Optional[str] = None
    precautions: Optional[str] = None
    unit: Optional[str] = "盒"
    stock: int = 0
    is_prescription: bool = False
    status: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    specification: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    approval_number: Optional[str] = None
    description: Optional[str] = None
    usage: Optional[str] = None
    precautions: Optional[str] = None
    unit: Optional[str] = None
    stock: Optional[int] = None
    is_prescription: Optional[bool] = None
    status: Optional[bool] = None


# ============= 处方管理（医生端 / 管理端） =============

class PrescriptionItemCreate(BaseModel):
    product_id: int
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None


class PrescriptionCreate(BaseModel):
    patient_id: int
    consultation_id: Optional[int] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    valid_until: Optional[datetime] = None
    items: List[PrescriptionItemCreate]


class PrescriptionUpdate(BaseModel):
    status: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    valid_until: Optional[datetime] = None


# ============= 订单管理（管理端） =============

class ShopOrderShip(BaseModel):
    tracking_number: Optional[str] = None
    note: Optional[str] = None


# ============= 设备绑定（患者端） =============

class DeviceBindRequest(BaseModel):
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None


class DeviceMeasurementUpload(BaseModel):
    type: MeasurementType
    value1: float
    value2: Optional[float] = None
    measured_at: Optional[datetime] = None


# ============= 患者/医生档案（管理端） =============

class AdminPatientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    chronic_diseases: Optional[str] = None
    allergies: Optional[str] = None
    doctor_id: Optional[int] = None


class AdminDoctorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    license_number: Optional[str] = None
    hospital: Optional[str] = None
    introduction: Optional[str] = None
    user_status: Optional[bool] = None


class AdminUserUpdate(BaseModel):
    """管理端更新用户基础信息"""
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    password: Optional[str] = None
    status: Optional[bool] = None
