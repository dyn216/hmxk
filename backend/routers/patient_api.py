from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import List, Optional
from datetime import datetime, timedelta
from math import ceil

from database import get_db
from models import (
    User, PatientProfile, DoctorProfile, Measurement, Medication, Guardian, Device,
    Message, Consultation, PatientAddress, ShopProduct, ShopCartItem, ShopOrder,
    ShopOrderItem, Prescription,
    UserRole, MeasurementType
)
from schemas import (
    LoginRequest, LoginResponse, MessageModel,
    MeasurementCreate, MeasurementOut, MeasurementStats,
    MedicationCreate, MedicationUpdate, MedicationOut, PatientProfileUpdate,
    GuardianCreate, GuardianOut,
    DeviceOut, PatientProfileBase, PatientProfileOut, DoctorDetail,
    PatientAddressCreate, PatientAddressUpdate, PatientAddressOut,
    ShopCartCreate, ShopCartUpdate, ShopCartItemOut, ShopOrderCreate, ShopOrderOut,
    ShopProductOut, PrescriptionOut, MessageCreate, MessageOut, ConsultationCreate, ConsultationOut,
    RegisterRequest, PasswordChange, PhoneChange,
    DeviceBindRequest, DeviceMeasurementUpload,
    VideoCallCreate, VideoCallEnd, VideoCallOut
)
from utils import (
    verify_password, create_access_token, ai_analyze_measurement, get_current_user_id,
    hash_password
)
from video_call import build_video_call_payload

router = APIRouter()


def get_current_patient_profile(authorization: str, db: Session):
    user_id = get_current_user_id(authorization)
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.PATIENT).first()
    if not user:
        raise HTTPException(status_code=403, detail="当前账号不是患者")
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    return user, profile


def build_doctor_detail(db: Session, doctor: DoctorProfile):
    patient_count = db.query(PatientProfile).filter(PatientProfile.doctor_id == doctor.id).count()
    consultation_count = db.query(Consultation).filter(Consultation.doctor_id == doctor.id).count()
    return {
        "id": doctor.id,
        "user_id": doctor.user_id,
        "user": doctor.user,
        "profile": doctor,
        "name": doctor.user.name if doctor.user else "",
        "avatar": doctor.user.avatar if doctor.user else None,
        "title": doctor.title,
        "department": doctor.department,
        "hospital": doctor.hospital,
        "specialty": doctor.introduction,
        "introduction": doctor.introduction,
        "patient_count": patient_count,
        "consultation_count": consultation_count,
        "online": bool(doctor.user and doctor.user.status),
        "can_video": bool(doctor.user and doctor.user.status)
    }


def resolve_doctor_profile(db: Session, doctor_identifier: Optional[int]):
    if doctor_identifier is None:
        return None
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_identifier).first()
    if doctor:
        return doctor
    return db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_identifier).first()


def resolve_doctor_user_first(db: Session, doctor_identifier: Optional[int]):
    if doctor_identifier is None:
        return None
    doctor = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_identifier).first()
    if doctor:
        return doctor
    return db.query(DoctorProfile).filter(DoctorProfile.id == doctor_identifier).first()


def build_patient_profile_detail(user: User, profile: PatientProfile, db: Session):
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == profile.doctor_id).first() if profile.doctor_id else None
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "age": profile.age,
        "gender": profile.gender,
        "address": profile.address,
        "emergency_contact": profile.emergency_contact,
        "emergency_phone": profile.emergency_phone,
        "height": profile.height,
        "weight": profile.weight,
        "chronic_diseases": profile.chronic_diseases,
        "allergies": profile.allergies,
        "doctor_id": profile.doctor_id,
        "created_at": profile.created_at,
        "user": user,
        "doctor": build_doctor_detail(db, doctor) if doctor else None
    }


def build_prescription_detail(prescription: Prescription):
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


def ensure_single_default_address(db: Session, patient_id: int, excluded_id: Optional[int] = None):
    query = db.query(PatientAddress).filter(PatientAddress.patient_id == patient_id)
    if excluded_id:
        query = query.filter(PatientAddress.id != excluded_id)
    query.update({"is_default": False})


def create_order_number():
    return datetime.now().strftime("SO%Y%m%d%H%M%S%f")


# ============= 认证相关 =============

@router.post("/login", response_model=LoginResponse)
def patient_login(body: LoginRequest, db: Session = Depends(get_db)):
    """患者登录"""
    user = db.query(User).filter(
        User.phone == body.phone,
        User.role == UserRole.PATIENT
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


@router.get("/profile")
def get_patient_profile(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """获取患者档案"""
    user, profile = get_current_patient_profile(authorization, db)
    return build_patient_profile_detail(user, profile, db)


@router.put("/profile")
def update_patient_profile(
    body: PatientProfileUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """更新患者档案"""
    user, profile = get_current_patient_profile(authorization, db)
    
    data = body.model_dump(exclude_unset=True)
    for key in ("name", "phone", "avatar"):
        if key in data:
            setattr(user, key, data.pop(key))
    for key, value in data.items():
        setattr(profile, key, value)
    
    user.updated_at = datetime.now()
    profile.updated_at = datetime.now()
    db.commit()
    
    return {"message": "档案更新成功"}


# ============= 监测数据相关 =============

@router.post("/measurements", response_model=MeasurementOut)
def create_measurement(
    body: MeasurementCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建监测数据（带AI分析）"""
    _, profile = get_current_patient_profile(authorization, db)
    
    # AI分析
    ai_result = ai_analyze_measurement(body.type, body.value1, body.value2)
    
    # 创建监测记录
    measurement = Measurement(
        patient_id=profile.id,
        type=body.type,
        value1=body.value1,
        value2=body.value2,
        measured_at=body.measured_at,
        device_id=body.device_id,
        notes=body.notes,
        risk_level=ai_result["risk_level"],
        ai_suggestion=ai_result["suggestion"]
    )
    
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    
    return measurement


@router.get("/measurements", response_model=List[MeasurementOut])
def list_measurements(
    authorization: str = Header(None),
    type: Optional[MeasurementType] = None,
    days: int = Query(7, description="查询最近N天的数据"),
    limit: int = Query(100, description="返回数据条数限制"),
    db: Session = Depends(get_db)
):
    """获取监测数据列表"""
    user_id = get_current_user_id(authorization)
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    
    # 构建查询
    query = db.query(Measurement).filter(
        Measurement.patient_id == profile.id,
        Measurement.measured_at >= datetime.now() - timedelta(days=days)
    )
    
    if type:
        query = query.filter(Measurement.type == type)
    
    measurements = query.order_by(desc(Measurement.measured_at)).limit(limit).all()
    return measurements


@router.get("/measurements/stats", response_model=MeasurementStats)
def get_measurement_stats(
    type: MeasurementType,
    authorization: str = Header(None),
    days: int = Query(7, description="统计最近N天的数据"),
    db: Session = Depends(get_db)
):
    """获取监测数据统计"""
    _, profile = get_current_patient_profile(authorization, db)
    
    # 查询指定时间范围的数据
    measurements = db.query(Measurement).filter(
        Measurement.patient_id == profile.id,
        Measurement.type == type,
        Measurement.measured_at >= datetime.now() - timedelta(days=days)
    ).all()
    
    if not measurements:
        return MeasurementStats(
            total_count=0,
            avg_value=None,
            max_value=None,
            min_value=None,
            latest_measurement=None
        )
    
    values = [m.value1 for m in measurements]
    latest = max(measurements, key=lambda m: m.measured_at)
    
    return MeasurementStats(
        total_count=len(measurements),
        avg_value=sum(values) / len(values),
        max_value=max(values),
        min_value=min(values),
        latest_measurement=latest
    )


@router.get("/measurements/{measurement_id}", response_model=MeasurementOut)
def get_measurement_detail(
    measurement_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """获取监测数据详情"""
    _, profile = get_current_patient_profile(authorization, db)
    measurement = db.query(Measurement).filter(
        Measurement.id == measurement_id,
        Measurement.patient_id == profile.id
    ).first()
    if not measurement:
        raise HTTPException(status_code=404, detail="监测记录不存在")
    return measurement


@router.delete("/measurements/{measurement_id}")
def delete_measurement(
    measurement_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """删除监测数据"""
    _, profile = get_current_patient_profile(authorization, db)
    measurement = db.query(Measurement).filter(
        Measurement.id == measurement_id,
        Measurement.patient_id == profile.id
    ).first()
    if not measurement:
        raise HTTPException(status_code=404, detail="监测记录不存在")
    db.delete(measurement)
    db.commit()
    return {"message": "监测记录删除成功"}


# ============= 用药管理相关 =============

@router.post("/medications", response_model=MedicationOut)
def create_medication(
    body: MedicationCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建用药记录"""
    user_id = get_current_user_id(authorization)
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    
    medication = Medication(
        patient_id=profile.id,
        **body.model_dump()
    )
    
    db.add(medication)
    db.commit()
    db.refresh(medication)
    
    return medication


@router.get("/medications", response_model=List[MedicationOut])
def list_medications(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """获取用药记录列表"""
    user_id = get_current_user_id(authorization)
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    
    medications = db.query(Medication).filter(
        Medication.patient_id == profile.id
    ).order_by(desc(Medication.created_at)).all()
    
    return medications


@router.put("/medications/{medication_id}", response_model=MedicationOut)
def update_medication(
    medication_id: int,
    body: MedicationUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """更新用药记录"""
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(medication, key, value)
    
    medication.updated_at = datetime.now()
    db.commit()
    db.refresh(medication)
    
    return medication


@router.delete("/medications/{medication_id}")
def delete_medication(
    medication_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """删除用药记录"""
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    
    db.delete(medication)
    db.commit()
    
    return {"message": "用药记录删除成功"}


# ============= 监护人相关 =============

@router.post("/guardians", response_model=GuardianOut)
def create_guardian(
    body: GuardianCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """创建监护人"""
    user_id = get_current_user_id(authorization)
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    
    guardian = Guardian(
        patient_id=profile.id,
        name=body.name,
        phone=body.phone,
        relation_type=body.relationship,
        can_view_data=body.can_view_data,
        can_receive_alerts=body.can_receive_alerts
    )
    
    db.add(guardian)
    db.commit()
    db.refresh(guardian)
    
    return guardian


@router.get("/guardians", response_model=List[GuardianOut])
def list_guardians(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """获取监护人列表"""
    user_id = get_current_user_id(authorization)
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    
    guardians = db.query(Guardian).filter(Guardian.patient_id == profile.id).all()
    return guardians


@router.delete("/guardians/{guardian_id}")
def delete_guardian(
    guardian_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """删除监护人"""
    guardian = db.query(Guardian).filter(Guardian.id == guardian_id).first()
    if not guardian:
        raise HTTPException(status_code=404, detail="监护人不存在")
    
    db.delete(guardian)
    db.commit()
    
    return {"message": "监护人删除成功"}


# ============= 设备相关 =============

@router.get("/devices", response_model=List[DeviceOut])
def list_devices(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """获取设备列表"""
    user_id = get_current_user_id(authorization)
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="患者档案不存在")
    
    devices = db.query(Device).filter(Device.patient_id == profile.id).all()
    return devices


@router.get("/addresses", response_model=List[PatientAddressOut])
def list_addresses(authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    return db.query(PatientAddress).filter(PatientAddress.patient_id == profile.id).order_by(desc(PatientAddress.is_default), desc(PatientAddress.created_at)).all()


@router.post("/addresses", response_model=PatientAddressOut)
def create_address(body: PatientAddressCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    has_address = db.query(PatientAddress).filter(PatientAddress.patient_id == profile.id).first() is not None
    if body.is_default or not has_address:
        ensure_single_default_address(db, profile.id)
    address = PatientAddress(patient_id=profile.id, **body.model_dump())
    if not has_address:
        address.is_default = True
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.put("/addresses/{address_id}", response_model=PatientAddressOut)
def update_address(address_id: int, body: PatientAddressUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    address = db.query(PatientAddress).filter(PatientAddress.id == address_id, PatientAddress.patient_id == profile.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="收货地址不存在")
    data = body.model_dump(exclude_unset=True)
    if data.get("is_default"):
        ensure_single_default_address(db, profile.id, address.id)
    for key, value in data.items():
        setattr(address, key, value)
    address.updated_at = datetime.now()
    db.commit()
    db.refresh(address)
    return address


@router.put("/addresses/{address_id}/default", response_model=PatientAddressOut)
def set_default_address(address_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    address = db.query(PatientAddress).filter(PatientAddress.id == address_id, PatientAddress.patient_id == profile.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="收货地址不存在")
    ensure_single_default_address(db, profile.id, address.id)
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address


@router.delete("/addresses/{address_id}")
def delete_address(address_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    address = db.query(PatientAddress).filter(PatientAddress.id == address_id, PatientAddress.patient_id == profile.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="收货地址不存在")
    was_default = address.is_default
    db.delete(address)
    db.commit()
    if was_default:
        next_address = db.query(PatientAddress).filter(PatientAddress.patient_id == profile.id).order_by(desc(PatientAddress.created_at)).first()
        if next_address:
            next_address.is_default = True
            db.commit()
    return {"message": "收货地址删除成功"}


@router.get("/shop/products")
def list_shop_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[bool] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ShopProduct)
    if status is not None:
        query = query.filter(ShopProduct.status == status)
    if category:
        query = query.filter(ShopProduct.category == category)
    total = query.count()
    total_pages = ceil(total / page_size) if total else 0
    items = query.order_by(desc(ShopProduct.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


@router.get("/shop/products/{product_id}", response_model=ShopProductOut)
def get_shop_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ShopProduct).filter(ShopProduct.id == product_id, ShopProduct.status == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product


@router.get("/shop/cart", response_model=List[ShopCartItemOut])
def list_cart_items(authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    return db.query(ShopCartItem).filter(ShopCartItem.patient_id == profile.id).order_by(desc(ShopCartItem.created_at)).all()


@router.post("/shop/cart", response_model=ShopCartItemOut)
def add_cart_item(body: ShopCartCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    if body.quantity < 1:
        raise HTTPException(status_code=400, detail="商品数量必须大于0")
    product = db.query(ShopProduct).filter(ShopProduct.id == body.product_id, ShopProduct.status == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    if product.is_prescription:
        raise HTTPException(status_code=400, detail="处方药需要医生处方后购买")
    if product.stock < body.quantity:
        raise HTTPException(status_code=400, detail="商品库存不足")
    item = db.query(ShopCartItem).filter(ShopCartItem.patient_id == profile.id, ShopCartItem.product_id == body.product_id).first()
    if item:
        item.quantity += body.quantity
        item.updated_at = datetime.now()
    else:
        item = ShopCartItem(patient_id=profile.id, product_id=body.product_id, quantity=body.quantity)
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/shop/cart")
def clear_cart(authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    db.query(ShopCartItem).filter(ShopCartItem.patient_id == profile.id).delete()
    db.commit()
    return {"message": "购物车已清空"}


@router.put("/shop/cart/{cart_id}", response_model=ShopCartItemOut)
def update_cart_item(cart_id: int, body: ShopCartUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    if body.quantity < 1:
        raise HTTPException(status_code=400, detail="商品数量必须大于0")
    item = db.query(ShopCartItem).filter(ShopCartItem.id == cart_id, ShopCartItem.patient_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="购物车商品不存在")
    if item.product.stock < body.quantity:
        raise HTTPException(status_code=400, detail="商品库存不足")
    item.quantity = body.quantity
    item.updated_at = datetime.now()
    db.commit()
    db.refresh(item)
    return item


@router.delete("/shop/cart/{cart_id}")
def delete_cart_item(cart_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    item = db.query(ShopCartItem).filter(ShopCartItem.id == cart_id, ShopCartItem.patient_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="购物车商品不存在")
    db.delete(item)
    db.commit()
    return {"message": "购物车商品已移除"}


@router.get("/shop/orders", response_model=List[ShopOrderOut])
def list_shop_orders(authorization: str = Header(None), status: Optional[str] = None, db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    query = db.query(ShopOrder).filter(ShopOrder.patient_id == profile.id)
    if status:
        query = query.filter(ShopOrder.status == status)
    return query.order_by(desc(ShopOrder.created_at)).all()


@router.post("/shop/orders", response_model=ShopOrderOut)
def create_shop_order(body: ShopOrderCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    if not body.items:
        raise HTTPException(status_code=400, detail="订单商品不能为空")
    prescription = None
    if body.prescription_id:
        prescription = db.query(Prescription).filter(Prescription.id == body.prescription_id, Prescription.patient_id == profile.id, Prescription.status == "approved").first()
        if not prescription:
            raise HTTPException(status_code=404, detail="可用处方不存在")
    product_ids = [item.product_id for item in body.items]
    products = db.query(ShopProduct).filter(ShopProduct.id.in_(product_ids), ShopProduct.status == True).all()
    product_map = {product.id: product for product in products}
    total_amount = 0.0
    order_items = []
    for item in body.items:
        if item.quantity < 1:
            raise HTTPException(status_code=400, detail="商品数量必须大于0")
        product = product_map.get(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        if product.is_prescription and not prescription:
            raise HTTPException(status_code=400, detail="处方药需要选择有效处方")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"{product.name}库存不足")
        total_amount += product.price * item.quantity
        order_items.append((product, item.quantity))
    order = ShopOrder(
        patient_id=profile.id,
        prescription_id=body.prescription_id,
        order_number=create_order_number(),
        status="pending",
        total_amount=round(total_amount, 2),
        receiver_name=body.receiver_name,
        receiver_phone=body.receiver_phone,
        receiver_address=body.receiver_address,
        remark=body.remark
    )
    db.add(order)
    db.flush()
    for product, quantity in order_items:
        db.add(ShopOrderItem(order_id=order.id, product_id=product.id, quantity=quantity, price=product.price))
        product.stock -= quantity
        product.sales_count += quantity
    db.query(ShopCartItem).filter(ShopCartItem.patient_id == profile.id, ShopCartItem.product_id.in_(product_ids)).delete(synchronize_session=False)
    db.commit()
    db.refresh(order)
    return order


@router.get("/shop/orders/{order_id}", response_model=ShopOrderOut)
def get_shop_order(order_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    order = db.query(ShopOrder).filter(ShopOrder.id == order_id, ShopOrder.patient_id == profile.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.put("/shop/orders/{order_id}/pay", response_model=ShopOrderOut)
def pay_shop_order(order_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    order = db.query(ShopOrder).filter(ShopOrder.id == order_id, ShopOrder.patient_id == profile.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="订单状态不允许支付")
    order.status = "paid"
    order.paid_at = datetime.now()
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


@router.put("/shop/orders/{order_id}/receive", response_model=ShopOrderOut)
def receive_shop_order(order_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    order = db.query(ShopOrder).filter(ShopOrder.id == order_id, ShopOrder.patient_id == profile.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "shipped":
        raise HTTPException(status_code=400, detail="订单状态不允许确认收货")
    order.status = "completed"
    order.delivered_at = datetime.now()
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


@router.put("/shop/orders/{order_id}/cancel", response_model=ShopOrderOut)
def cancel_shop_order(order_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    order = db.query(ShopOrder).filter(ShopOrder.id == order_id, ShopOrder.patient_id == profile.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in ("pending", "paid"):
        raise HTTPException(status_code=400, detail="订单状态不允许取消")
    if order.status in ("pending", "paid"):
        for item in order.items:
            item.product.stock += item.quantity
            item.product.sales_count = max(0, item.product.sales_count - item.quantity)
    order.status = "cancelled"
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


@router.delete("/shop/orders/{order_id}", response_model=ShopOrderOut)
def delete_shop_order(order_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    return cancel_shop_order(order_id, authorization, db)


@router.get("/prescriptions", response_model=List[PrescriptionOut])
def list_prescriptions(authorization: str = Header(None), status: Optional[str] = None, db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    query = db.query(Prescription).filter(Prescription.patient_id == profile.id)
    if status:
        query = query.filter(Prescription.status == status)
    return [build_prescription_detail(item) for item in query.order_by(desc(Prescription.created_at)).all()]


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionOut)
def get_prescription(prescription_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id, Prescription.patient_id == profile.id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="处方不存在")
    return build_prescription_detail(prescription)


# ============= 医生与问诊相关 =============

@router.get("/doctors", response_model=List[DoctorDetail])
def list_doctors(
    search: Optional[str] = None,
    limit: int = Query(50, description="返回数据条数限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取医生列表"""
    query = db.query(DoctorProfile).join(User).filter(User.role == UserRole.DOCTOR, User.status == True)
    if search:
        query = query.filter(or_(User.name.like(f"%{search}%"), DoctorProfile.department.like(f"%{search}%"), DoctorProfile.hospital.like(f"%{search}%")))
    doctors = query.options().offset(offset).limit(limit).all()
    return [build_doctor_detail(db, doctor) for doctor in doctors]


@router.get("/doctor/profile", response_model=DoctorDetail)
def get_doctor_profile_compat(
    user_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    doctor = resolve_doctor_profile(db, doctor_id) if doctor_id is not None else resolve_doctor_user_first(db, user_id)
    if not doctor or not doctor.user or not doctor.user.status:
        raise HTTPException(status_code=404, detail="医生不存在")
    return build_doctor_detail(db, doctor)


@router.get("/consultations", response_model=List[ConsultationOut])
def list_consultations(
    authorization: str = Header(None),
    status: Optional[str] = None,
    days: int = Query(30, description="查询最近N天的数据"),
    db: Session = Depends(get_db)
):
    """获取患者问诊记录"""
    _, profile = get_current_patient_profile(authorization, db)
    query = db.query(Consultation).filter(
        Consultation.patient_id == profile.id,
        Consultation.scheduled_time >= datetime.now() - timedelta(days=days)
    )
    if status:
        query = query.filter(Consultation.status == status)
    return query.order_by(desc(Consultation.scheduled_time)).all()


@router.post("/consultations", response_model=ConsultationOut)
def create_consultation(body: ConsultationCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """创建患者问诊预约"""
    _, profile = get_current_patient_profile(authorization, db)
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == body.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    consultation = Consultation(
        patient_id=profile.id,
        doctor_id=doctor.id,
        scheduled_time=body.scheduled_time,
        chief_complaint=body.chief_complaint,
        status="pending"
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return consultation


@router.post("/video-calls", response_model=VideoCallOut)
def create_video_call(body: VideoCallCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user, profile = get_current_patient_profile(authorization, db)
    notify_doctor = False
    if body.consultation_id:
        consultation = db.query(Consultation).filter(
            Consultation.id == body.consultation_id,
            Consultation.patient_id == profile.id
        ).first()
        if not consultation:
            raise HTTPException(status_code=404, detail="视频问诊不存在")
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == consultation.doctor_id).first()
        if body.doctor_id and doctor and doctor.id != body.doctor_id:
            raise HTTPException(status_code=400, detail="医生信息不匹配")
    else:
        if not body.doctor_id:
            raise HTTPException(status_code=400, detail="缺少医生信息")
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == body.doctor_id).first()
        if not doctor or not doctor.user or not doctor.user.status:
            raise HTTPException(status_code=404, detail="医生不存在或不可用")
        consultation = Consultation(
            patient_id=profile.id,
            doctor_id=doctor.id,
            scheduled_time=datetime.now(),
            start_time=datetime.now(),
            chief_complaint=body.chief_complaint or "视频问诊",
            status="ongoing"
        )
        db.add(consultation)
        db.flush()
        notify_doctor = True
    if not doctor or not doctor.user or not doctor.user.status:
        raise HTTPException(status_code=404, detail="医生不存在或不可用")
    if consultation.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="当前问诊已结束")
    if consultation.status != "ongoing":
        consultation.status = "ongoing"
        notify_doctor = True
    if not consultation.start_time:
        consultation.start_time = datetime.now()
    consultation.updated_at = datetime.now()
    if notify_doctor:
        db.add(Message(
            sender_id=user.id,
            receiver_id=doctor.user_id,
            content="患者发起了视频问诊，请及时加入。问诊编号：" + str(consultation.id),
            message_type="video_call",
            doctor_id=doctor.id
        ))
    db.commit()
    db.refresh(consultation)
    return build_video_call_payload(consultation, "patient", doctor, profile)


@router.get("/video-calls/{consultation_id}", response_model=VideoCallOut)
def get_video_call(consultation_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.patient_id == profile.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="视频问诊不存在")
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == consultation.doctor_id).first()
    return build_video_call_payload(consultation, "patient", doctor, profile)


@router.put("/video-calls/{consultation_id}/end", response_model=VideoCallOut)
def end_video_call(consultation_id: int, body: Optional[VideoCallEnd] = None, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, profile = get_current_patient_profile(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.patient_id == profile.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="视频问诊不存在")
    if consultation.status not in ("completed", "cancelled"):
        consultation.status = "completed"
        consultation.end_time = datetime.now()
    if body:
        notes = []
        if consultation.notes:
            notes.append(consultation.notes)
        if body.notes:
            notes.append(body.notes)
        if body.duration:
            notes.append("通话时长：" + body.duration)
        if notes:
            consultation.notes = "\n".join(notes)
    consultation.updated_at = datetime.now()
    db.commit()
    db.refresh(consultation)
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == consultation.doctor_id).first()
    return build_video_call_payload(consultation, "patient", doctor, profile)


# ============= 消息与报告相关 =============

@router.get("/messages", response_model=List[MessageOut])
def list_messages(
    authorization: str = Header(None),
    doctor_id: Optional[int] = None,
    doctor_user_id: Optional[int] = None,
    other_user_id: Optional[int] = None,
    unread_only: bool = Query(False, description="只显示未读消息"),
    limit: int = Query(50, description="返回数据条数限制"),
    db: Session = Depends(get_db)
):
    """获取患者消息列表"""
    user, _ = get_current_patient_profile(authorization, db)
    query = db.query(Message).filter(or_(Message.sender_id == user.id, Message.receiver_id == user.id))
    if doctor_id or doctor_user_id or other_user_id:
        if doctor_user_id:
            doctor = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user_id).first()
        elif other_user_id:
            doctor = resolve_doctor_user_first(db, other_user_id)
        else:
            doctor = resolve_doctor_profile(db, doctor_id)
        if not doctor:
            if other_user_id:
                query = query.filter(or_(Message.sender_id == other_user_id, Message.receiver_id == other_user_id))
            else:
                raise HTTPException(status_code=404, detail="医生不存在")
        else:
            query = query.filter(or_(Message.sender_id == doctor.user_id, Message.receiver_id == doctor.user_id))
    if unread_only:
        query = query.filter(Message.receiver_id == user.id, Message.is_read == False)
    return query.order_by(desc(Message.created_at)).limit(limit).all()


@router.post("/messages", response_model=MessageOut)
def send_message(body: MessageCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """发送患者消息"""
    user, _ = get_current_patient_profile(authorization, db)
    receiver_id = body.receiver_id
    doctor_id = None
    if body.doctor_id:
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == body.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="医生不存在")
        receiver_id = doctor.user_id
        doctor_id = doctor.id
    if not receiver_id:
        raise HTTPException(status_code=400, detail="缺少接收人")
    message = Message(sender_id=user.id, receiver_id=receiver_id, content=body.content, message_type=body.message_type, doctor_id=doctor_id)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/notification/messages", response_model=List[MessageOut])
def list_notification_messages(
    authorization: str = Header(None),
    doctor_id: Optional[int] = None,
    doctor_user_id: Optional[int] = None,
    other_user_id: Optional[int] = None,
    unread_only: bool = Query(False, description="只显示未读消息"),
    limit: int = Query(50, description="返回数据条数限制"),
    db: Session = Depends(get_db)
):
    return list_messages(authorization, doctor_id, doctor_user_id, other_user_id, unread_only, limit, db)


@router.post("/notification/messages", response_model=MessageOut)
def send_notification_message(body: MessageCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    if body.receiver_id and not body.doctor_id:
        doctor = resolve_doctor_profile(db, body.receiver_id)
        if doctor:
            body = MessageCreate(doctor_id=doctor.id, content=body.content, message_type=body.message_type)
    return send_message(body, authorization, db)


@router.get("/health-report")
def get_health_report(authorization: str = Header(None), days: int = Query(30), db: Session = Depends(get_db)):
    """获取患者健康报告"""
    _, profile = get_current_patient_profile(authorization, db)
    measurements = db.query(Measurement).filter(
        Measurement.patient_id == profile.id,
        Measurement.measured_at >= datetime.now() - timedelta(days=days)
    ).order_by(desc(Measurement.measured_at)).all()
    return {
        "patient_id": profile.id,
        "days": days,
        "total_measurements": len(measurements),
        "latest_measurement": measurements[0] if measurements else None,
        "measurements": measurements
    }


# ============= 账号注册与安全 =============

@router.post("/register", response_model=LoginResponse)
def patient_register(body: RegisterRequest, db: Session = Depends(get_db)):
    """患者注册：创建用户与档案，注册即登录返回 token"""
    if not body.phone or not body.password or not body.name:
        raise HTTPException(status_code=400, detail="手机号、密码、姓名均不能为空")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少 6 位")
    existing = db.query(User).filter(User.phone == body.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="手机号已注册")
    user = User(
        phone=body.phone,
        password=hash_password(body.password),
        name=body.name,
        role=UserRole.PATIENT,
        status=True,
        last_login=datetime.now()
    )
    db.add(user)
    db.flush()
    profile = PatientProfile(
        user_id=user.id,
        age=body.age,
        gender=body.gender
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return LoginResponse(token=token, user_id=user.id, role=user.role, name=user.name, avatar=user.avatar)


@router.put("/password")
def change_password(body: PasswordChange, authorization: str = Header(None), db: Session = Depends(get_db)):
    """修改密码"""
    user, _ = get_current_patient_profile(authorization, db)
    if not verify_password(body.old_password, user.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少 6 位")
    user.password = hash_password(body.new_password)
    user.updated_at = datetime.now()
    db.commit()
    return {"message": "密码修改成功"}


@router.put("/phone")
def change_phone(body: PhoneChange, authorization: str = Header(None), db: Session = Depends(get_db)):
    """修改手机号：要求当前账号密码验证"""
    user, _ = get_current_patient_profile(authorization, db)
    if not verify_password(body.password, user.password):
        raise HTTPException(status_code=400, detail="密码错误")
    if db.query(User).filter(User.phone == body.new_phone, User.id != user.id).first():
        raise HTTPException(status_code=400, detail="新手机号已被占用")
    user.phone = body.new_phone
    user.updated_at = datetime.now()
    db.commit()
    return {"message": "手机号修改成功", "phone": user.phone}


@router.delete("/account")
def deactivate_account(authorization: str = Header(None), db: Session = Depends(get_db)):
    """注销账号：禁用账号并清除手机号占用"""
    user, profile = get_current_patient_profile(authorization, db)
    # 软删除：禁用账号；同时把手机号改为带前缀的失效形式以释放占用
    user.status = False
    user.phone = f"deleted_{user.id}_{user.phone}"[:20]
    user.updated_at = datetime.now()
    db.commit()
    return {"message": "账号已注销"}


# ============= 消息已读 / 未读数 =============

@router.put("/messages/{message_id}/read")
def mark_message_read(message_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """标记单条消息为已读（仅本人接收的消息）"""
    user, _ = get_current_patient_profile(authorization, db)
    message = db.query(Message).filter(Message.id == message_id, Message.receiver_id == user.id).first()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    if not message.is_read:
        message.is_read = True
        message.read_at = datetime.now()
        db.commit()
    return {"message": "消息已标记为已读"}


@router.put("/notification/messages/{message_id}/read")
def mark_notification_message_read(message_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    return mark_message_read(message_id, authorization, db)


@router.put("/messages/read-all")
def mark_all_messages_read(authorization: str = Header(None), db: Session = Depends(get_db)):
    """全部消息标记为已读"""
    user, _ = get_current_patient_profile(authorization, db)
    now = datetime.now()
    count = db.query(Message).filter(
        Message.receiver_id == user.id,
        Message.is_read == False
    ).update({"is_read": True, "read_at": now})
    db.commit()
    return {"message": "全部已读", "updated": count}


@router.get("/messages/unread-count")
def get_unread_count(authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取未读消息数量"""
    user, _ = get_current_patient_profile(authorization, db)
    count = db.query(Message).filter(
        Message.receiver_id == user.id,
        Message.is_read == False
    ).count()
    return {"unread_count": count}


# ============= 问诊详情 / 取消 =============

@router.get("/consultations/{consultation_id}", response_model=ConsultationOut)
def get_consultation_detail(consultation_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取问诊详情"""
    _, profile = get_current_patient_profile(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.patient_id == profile.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="问诊记录不存在")
    return consultation


@router.put("/consultations/{consultation_id}/cancel", response_model=ConsultationOut)
def cancel_consultation(consultation_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """取消问诊预约（仅 pending / confirmed 状态可取消）"""
    _, profile = get_current_patient_profile(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.patient_id == profile.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="问诊记录不存在")
    if consultation.status not in ("pending", "confirmed"):
        raise HTTPException(status_code=400, detail="当前状态不允许取消")
    consultation.status = "cancelled"
    consultation.updated_at = datetime.now()
    db.commit()
    db.refresh(consultation)
    return consultation


# ============= 设备绑定 / 解绑 / 数据上报 =============

@router.post("/devices/bind", response_model=DeviceOut)
def bind_device(body: DeviceBindRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    """绑定设备到当前患者"""
    _, profile = get_current_patient_profile(authorization, db)
    device = db.query(Device).filter(Device.device_id == body.device_id).first()
    if device:
        if device.patient_id and device.patient_id != profile.id:
            raise HTTPException(status_code=400, detail="设备已被其他用户绑定")
        device.patient_id = profile.id
        device.device_name = body.device_name or device.device_name
        device.device_type = body.device_type or device.device_type
        device.model = body.model or device.model
        device.status = device.status or "online"
        device.updated_at = datetime.now()
    else:
        device = Device(
            device_id=body.device_id,
            device_name=body.device_name,
            device_type=body.device_type,
            model=body.model,
            patient_id=profile.id,
            status="online"
        )
        db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/devices/{device_pk}")
def unbind_device(device_pk: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """解绑设备（仅解除归属，不删除设备记录）"""
    _, profile = get_current_patient_profile(authorization, db)
    device = db.query(Device).filter(Device.id == device_pk, Device.patient_id == profile.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    device.patient_id = None
    device.status = "offline"
    device.updated_at = datetime.now()
    db.commit()
    return {"message": "设备已解绑"}


@router.post("/devices/{device_id_str}/measurements", response_model=MeasurementOut)
def upload_device_measurement(
    device_id_str: str,
    body: DeviceMeasurementUpload,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """设备上报监测数据（设备业务编号入参，自动归属至绑定患者）"""
    _, profile = get_current_patient_profile(authorization, db)
    device = db.query(Device).filter(
        Device.device_id == device_id_str,
        Device.patient_id == profile.id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备未绑定到当前患者")
    measured_at = body.measured_at or datetime.now()
    ai_result = ai_analyze_measurement(body.type, body.value1, body.value2)
    measurement = Measurement(
        patient_id=profile.id,
        type=body.type,
        value1=body.value1,
        value2=body.value2,
        measured_at=measured_at,
        device_id=device.device_id,
        risk_level=ai_result["risk_level"],
        ai_suggestion=ai_result["suggestion"]
    )
    db.add(measurement)
    device.last_sync = measured_at
    device.status = "online"
    db.commit()
    db.refresh(measurement)
    return measurement


# ============= 客服消息 =============

@router.post("/support/messages", response_model=MessageOut)
def send_support_message(body: MessageCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """发送客服消息：默认收件人为最早创建的管理员账号"""
    user, _ = get_current_patient_profile(authorization, db)
    admin = db.query(User).filter(User.role == UserRole.ADMIN, User.status == True).order_by(User.id).first()
    if not admin:
        raise HTTPException(status_code=503, detail="暂无客服在线")
    message = Message(
        sender_id=user.id,
        receiver_id=admin.id,
        content=body.content,
        message_type=body.message_type or "text"
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
