from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import (
    User, PatientProfile, DoctorProfile, Measurement, Message,
    Consultation, FollowUp, News, Prescription, PrescriptionItem, ShopProduct,
    UserRole, MeasurementType
)
from schemas import (
    LoginRequest, LoginResponse,
    PatientDetail, MeasurementOut,
    MessageCreate, MessageOut,
    ConsultationCreate, ConsultationUpdate, ConsultationOut,
    FollowUpCreate, FollowUpUpdate, FollowUpOut,
    NewsOut, DoctorDetail, DoctorProfileBase,
    PasswordChange, PrescriptionCreate, PrescriptionUpdate, PrescriptionOut,
    VideoCallEnd, VideoCallOut
)
from utils import verify_password, create_access_token, get_current_user_id, hash_password
from video_call import build_video_call_payload

router = APIRouter()


def get_current_doctor(authorization: str, db: Session):
    user_id = get_current_user_id(authorization)
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.DOCTOR).first()
    if not user:
        raise HTTPException(status_code=403, detail="当前账号不是医生")
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="医生档案不存在")
    return user, profile


def build_patient_detail(db: Session, patient: PatientProfile):
    total_measurements = db.query(Measurement).filter(Measurement.patient_id == patient.id).count()
    latest_measurement = db.query(Measurement).filter(
        Measurement.patient_id == patient.id
    ).order_by(desc(Measurement.measured_at)).first()
    return PatientDetail(
        id=patient.id,
        user=patient.user,
        profile=patient,
        total_measurements=total_measurements,
        latest_measurement=latest_measurement.measured_at if latest_measurement else None
    )


@router.post("/login", response_model=LoginResponse)
def doctor_login(body: LoginRequest, db: Session = Depends(get_db)):
    """医生登录"""
    user = db.query(User).filter(
        User.phone == body.phone,
        User.role == UserRole.DOCTOR
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.password and not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="密码错误")
    if not user.status:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    user.last_login = datetime.now()
    db.commit()
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return LoginResponse(token=token, user_id=user.id, role=user.role, name=user.name, avatar=user.avatar)


@router.get("/profile", response_model=DoctorDetail)
def get_doctor_profile(authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取医生详细信息"""
    user, profile = get_current_doctor(authorization, db)
    patient_count = db.query(PatientProfile).filter(PatientProfile.doctor_id == profile.id).count()
    consultation_count = db.query(Consultation).filter(Consultation.doctor_id == profile.id).count()
    return DoctorDetail(id=profile.id, user=user, profile=profile, patient_count=patient_count, consultation_count=consultation_count)


@router.put("/profile", response_model=DoctorDetail)
def update_doctor_profile(body: DoctorProfileBase, authorization: str = Header(None), db: Session = Depends(get_db)):
    """更新医生详细信息"""
    user, profile = get_current_doctor(authorization, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    profile.updated_at = datetime.now()
    db.commit()
    db.refresh(profile)
    patient_count = db.query(PatientProfile).filter(PatientProfile.doctor_id == profile.id).count()
    consultation_count = db.query(Consultation).filter(Consultation.doctor_id == profile.id).count()
    return DoctorDetail(id=profile.id, user=user, profile=profile, patient_count=patient_count, consultation_count=consultation_count)


@router.get("/stats")
def get_work_stats(authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取医生工作统计"""
    user, profile = get_current_doctor(authorization, db)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_consultations = db.query(Consultation).filter(
        Consultation.doctor_id == profile.id,
        Consultation.scheduled_time >= today_start
    ).count()
    pending_patients = db.query(PatientProfile).filter(PatientProfile.doctor_id == profile.id).count()
    unread_messages = db.query(Message).filter(Message.receiver_id == user.id, Message.is_read == False).count()
    return {
        "today_consultations": today_consultations,
        "pending_patients": pending_patients,
        "satisfaction_rate": 0,
        "unread_messages": unread_messages,
        "patient_count": pending_patients,
        "report_count": db.query(Measurement.patient_id).distinct().count(),
        "consultation_count": db.query(Consultation).filter(Consultation.doctor_id == profile.id).count()
    }


@router.get("/patients", response_model=List[PatientDetail])
def list_patients(
    authorization: str = Header(None),
    search: Optional[str] = None,
    limit: int = Query(50, description="返回数据条数限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取医生管理的患者列表"""
    _, doctor_profile = get_current_doctor(authorization, db)
    query = db.query(PatientProfile).filter(
        PatientProfile.doctor_id == doctor_profile.id
    ).options(joinedload(PatientProfile.user))
    if search:
        query = query.join(User).filter(or_(User.name.like(f"%{search}%"), User.phone.like(f"%{search}%")))
    patients = query.offset(offset).limit(limit).all()
    return [build_patient_detail(db, patient) for patient in patients]


@router.get("/patients/{patient_id}", response_model=PatientDetail)
def get_patient_detail(patient_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取患者详情"""
    _, doctor_profile = get_current_doctor(authorization, db)
    patient = db.query(PatientProfile).filter(
        PatientProfile.id == patient_id,
        PatientProfile.doctor_id == doctor_profile.id
    ).options(joinedload(PatientProfile.user)).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    return build_patient_detail(db, patient)


@router.get("/patients/{patient_id}/measurements", response_model=List[MeasurementOut])
def get_patient_measurements(
    patient_id: int,
    authorization: str = Header(None),
    type: Optional[MeasurementType] = None,
    days: int = Query(7, description="查询最近N天的数据"),
    limit: int = Query(100, description="返回数据条数限制"),
    db: Session = Depends(get_db)
):
    """获取患者的监测数据"""
    _, doctor_profile = get_current_doctor(authorization, db)
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id, PatientProfile.doctor_id == doctor_profile.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    query = db.query(Measurement).filter(
        Measurement.patient_id == patient_id,
        Measurement.measured_at >= datetime.now() - timedelta(days=days)
    )
    if type:
        query = query.filter(Measurement.type == type)
    return query.order_by(desc(Measurement.measured_at)).limit(limit).all()


@router.get("/patients/{patient_id}/report")
def get_patient_report(patient_id: int, authorization: str = Header(None), days: int = Query(30), db: Session = Depends(get_db)):
    """获取患者健康报告"""
    _, doctor_profile = get_current_doctor(authorization, db)
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id, PatientProfile.doctor_id == doctor_profile.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    measurements = db.query(Measurement).filter(
        Measurement.patient_id == patient_id,
        Measurement.measured_at >= datetime.now() - timedelta(days=days)
    ).order_by(desc(Measurement.measured_at)).all()
    return {
        "patient_id": patient_id,
        "days": days,
        "total_measurements": len(measurements),
        "latest_measurement": measurements[0] if measurements else None,
        "measurements": measurements
    }


@router.post("/messages", response_model=MessageOut)
def send_message(body: MessageCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """发送消息"""
    user, doctor_profile = get_current_doctor(authorization, db)
    receiver_id = body.receiver_id
    if body.patient_id:
        patient = db.query(PatientProfile).filter(
            PatientProfile.id == body.patient_id,
            PatientProfile.doctor_id == doctor_profile.id
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="患者不存在")
        receiver_id = patient.user_id
    if not receiver_id:
        raise HTTPException(status_code=400, detail="缺少接收人")
    message = Message(sender_id=user.id, receiver_id=receiver_id, content=body.content, message_type=body.message_type, doctor_id=doctor_profile.id)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/messages", response_model=List[MessageOut])
def list_messages(
    authorization: str = Header(None),
    patient_id: Optional[int] = None,
    unread_only: bool = Query(False, description="只显示未读消息"),
    limit: int = Query(50, description="返回数据条数限制"),
    db: Session = Depends(get_db)
):
    """获取消息列表"""
    user, doctor_profile = get_current_doctor(authorization, db)
    query = db.query(Message).filter(or_(Message.sender_id == user.id, Message.receiver_id == user.id))
    if patient_id:
        patient = db.query(PatientProfile).filter(
            PatientProfile.id == patient_id,
            PatientProfile.doctor_id == doctor_profile.id
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="患者不存在")
        query = query.filter(or_(Message.sender_id == patient.user_id, Message.receiver_id == patient.user_id))
    if unread_only:
        query = query.filter(Message.receiver_id == user.id, Message.is_read == False)
    return query.order_by(desc(Message.created_at)).limit(limit).all()


@router.put("/messages/{message_id}/read")
def mark_message_read(message_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """标记消息为已读"""
    user, _ = get_current_doctor(authorization, db)
    message = db.query(Message).filter(Message.id == message_id, Message.receiver_id == user.id).first()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    message.is_read = True
    message.read_at = datetime.now()
    db.commit()
    return {"message": "消息已标记为已读"}


@router.post("/consultations", response_model=ConsultationOut)
def create_consultation(body: ConsultationCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """创建问诊预约"""
    _, doctor_profile = get_current_doctor(authorization, db)
    if body.patient_id:
        patient = db.query(PatientProfile).filter(
            PatientProfile.id == body.patient_id,
            PatientProfile.doctor_id == doctor_profile.id
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="患者不存在")
    consultation = Consultation(patient_id=body.patient_id, doctor_id=doctor_profile.id, scheduled_time=body.scheduled_time, chief_complaint=body.chief_complaint, status="pending")
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return consultation


@router.get("/consultations", response_model=List[ConsultationOut])
def list_consultations(
    authorization: str = Header(None),
    status: Optional[str] = None,
    days: int = Query(30, description="查询最近N天的数据"),
    db: Session = Depends(get_db)
):
    """获取问诊列表"""
    _, doctor_profile = get_current_doctor(authorization, db)
    query = db.query(Consultation).filter(
        Consultation.doctor_id == doctor_profile.id,
        Consultation.scheduled_time >= datetime.now() - timedelta(days=days)
    )
    if status:
        query = query.filter(Consultation.status == status)
    return query.order_by(desc(Consultation.scheduled_time)).all()


@router.get("/consultations/{consultation_id}", response_model=ConsultationOut)
def get_consultation_detail(consultation_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取问诊详情"""
    _, doctor_profile = get_current_doctor(authorization, db)
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id, Consultation.doctor_id == doctor_profile.id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="问诊记录不存在")
    return consultation


@router.put("/consultations/{consultation_id}", response_model=ConsultationOut)
def update_consultation(consultation_id: int, body: ConsultationUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """更新问诊记录"""
    _, doctor_profile = get_current_doctor(authorization, db)
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id, Consultation.doctor_id == doctor_profile.id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="问诊记录不存在")
    data = body.model_dump(exclude_unset=True)
    if "patient_id" in data and data["patient_id"]:
        patient = db.query(PatientProfile).filter(
            PatientProfile.id == data["patient_id"],
            PatientProfile.doctor_id == doctor_profile.id
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="患者不存在")
    for key, value in data.items():
        setattr(consultation, key, value)
    consultation.updated_at = datetime.now()
    db.commit()
    db.refresh(consultation)
    return consultation


@router.get("/schedules")
def list_schedules(
    authorization: str = Header(None),
    date: Optional[str] = None,
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    """获取日程列表"""
    _, doctor_profile = get_current_doctor(authorization, db)
    if date:
        start_time = datetime.fromisoformat(date)
        end_time = start_time + timedelta(days=1)
    else:
        start_time = datetime.now() - timedelta(days=days)
        end_time = datetime.now() + timedelta(days=days)
    consultations = db.query(Consultation).filter(
        Consultation.doctor_id == doctor_profile.id,
        Consultation.scheduled_time >= start_time,
        Consultation.scheduled_time < end_time
    ).order_by(Consultation.scheduled_time).all()
    follow_ups = db.query(FollowUp).filter(
        FollowUp.doctor_id == doctor_profile.id,
        FollowUp.scheduled_date >= start_time,
        FollowUp.scheduled_date < end_time
    ).order_by(FollowUp.scheduled_date).all()
    status_text_map = {
        "pending": "待确认",
        "confirmed": "已确认",
        "cancelled": "已取消",
        "completed": "已完成",
        "ongoing": "进行中"
    }
    schedules = []
    for consultation in consultations:
        patient = db.query(PatientProfile).filter(PatientProfile.id == consultation.patient_id).first() if consultation.patient_id else None
        schedules.append({
            "id": consultation.id,
            "time": consultation.scheduled_time.strftime("%H:%M") if consultation.scheduled_time else "",
            "status": consultation.status,
            "statusText": status_text_map.get(consultation.status, consultation.status or ""),
            "patientName": patient.user.name if patient and patient.user else "",
            "patientAge": patient.age if patient else None,
            "type": "consultation",
            "typeText": "问诊",
            "title": "问诊安排",
            "description": consultation.chief_complaint or "",
            "note": consultation.notes or consultation.chief_complaint or ""
        })
    for follow_up in follow_ups:
        patient = db.query(PatientProfile).filter(PatientProfile.id == follow_up.patient_id).first() if follow_up.patient_id else None
        schedules.append({
            "id": -follow_up.id,
            "time": follow_up.scheduled_date.strftime("%H:%M") if follow_up.scheduled_date else "",
            "status": "completed" if follow_up.completed else "follow_up",
            "statusText": "已完成" if follow_up.completed else "随访",
            "patientName": patient.user.name if patient and patient.user else "",
            "patientAge": patient.age if patient else None,
            "type": "follow-up",
            "typeText": "随访",
            "title": "随访安排",
            "description": follow_up.notes or "",
            "note": follow_up.notes or ""
        })
    return schedules


@router.put("/schedules/{schedule_id}", response_model=ConsultationOut)
def update_schedule(schedule_id: int, body: ConsultationUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """更新日程"""
    return update_consultation(schedule_id, body, authorization, db)


@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """删除日程"""
    _, doctor_profile = get_current_doctor(authorization, db)
    if schedule_id < 0:
        follow_up = db.query(FollowUp).filter(FollowUp.id == abs(schedule_id), FollowUp.doctor_id == doctor_profile.id).first()
        if not follow_up:
            raise HTTPException(status_code=404, detail="日程不存在")
        db.delete(follow_up)
        db.commit()
        return {"message": "日程删除成功"}
    consultation = db.query(Consultation).filter(Consultation.id == schedule_id, Consultation.doctor_id == doctor_profile.id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="日程不存在")
    db.delete(consultation)
    db.commit()
    return {"message": "日程删除成功"}


@router.post("/follow-ups", response_model=FollowUpOut)
def create_follow_up(body: FollowUpCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """创建随访计划"""
    _, doctor_profile = get_current_doctor(authorization, db)
    follow_up = FollowUp(patient_id=body.patient_id, doctor_id=doctor_profile.id, scheduled_date=body.scheduled_date, follow_up_type=body.follow_up_type, notes=body.notes)
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    return follow_up


@router.get("/follow-ups", response_model=List[FollowUpOut])
def list_follow_ups(
    authorization: str = Header(None),
    completed: Optional[bool] = None,
    days: int = Query(30, description="查询最近N天的数据"),
    db: Session = Depends(get_db)
):
    """获取随访列表"""
    _, doctor_profile = get_current_doctor(authorization, db)
    query = db.query(FollowUp).filter(
        FollowUp.doctor_id == doctor_profile.id,
        FollowUp.scheduled_date >= datetime.now() - timedelta(days=days)
    )
    if completed is not None:
        query = query.filter(FollowUp.completed == completed)
    return query.order_by(desc(FollowUp.scheduled_date)).all()


@router.put("/follow-ups/{follow_up_id}", response_model=FollowUpOut)
def update_follow_up(follow_up_id: int, body: FollowUpUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """更新随访记录"""
    _, doctor_profile = get_current_doctor(authorization, db)
    follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id, FollowUp.doctor_id == doctor_profile.id).first()
    if not follow_up:
        raise HTTPException(status_code=404, detail="随访记录不存在")
    if body.completed:
        follow_up.completed = True
        follow_up.completed_at = datetime.now()
    if body.result:
        follow_up.result = body.result
    follow_up.updated_at = datetime.now()
    db.commit()
    db.refresh(follow_up)
    return follow_up


@router.get("/reports")
def list_reports(authorization: str = Header(None), limit: int = Query(50), db: Session = Depends(get_db)):
    """获取报告列表"""
    _, doctor_profile = get_current_doctor(authorization, db)
    patients = db.query(PatientProfile).filter(PatientProfile.doctor_id == doctor_profile.id).limit(limit).all()
    reports = []
    for patient in patients:
        latest = db.query(Measurement).filter(Measurement.patient_id == patient.id).order_by(desc(Measurement.measured_at)).first()
        if latest:
            reports.append({
                "id": latest.id,
                "patient_id": patient.id,
                "patient_name": patient.user.name if patient.user else "",
                "created_at": latest.created_at,
                "risk_level": latest.risk_level,
                "summary": latest.ai_suggestion
            })
    return reports


@router.get("/reports/{report_id}")
def get_report_detail(report_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取报告详情"""
    _, doctor_profile = get_current_doctor(authorization, db)
    measurement = db.query(Measurement).join(PatientProfile, Measurement.patient_id == PatientProfile.id).filter(
        Measurement.id == report_id,
        PatientProfile.doctor_id == doctor_profile.id
    ).first()
    if not measurement:
        raise HTTPException(status_code=404, detail="报告不存在")
    return measurement


def _build_prescription_detail(prescription: Prescription) -> dict:
    """组装处方详情响应（与 PrescriptionOut 模型一致）"""
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


@router.post("/prescriptions", response_model=PrescriptionOut)
def create_prescription(body: PrescriptionCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """医生开具处方：落库到 Prescription 与 PrescriptionItem"""
    _, doctor_profile = get_current_doctor(authorization, db)
    patient = db.query(PatientProfile).filter(PatientProfile.id == body.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    if not body.items:
        raise HTTPException(status_code=400, detail="处方至少包含一个药品")
    # 校验关联问诊归属
    if body.consultation_id:
        consultation = db.query(Consultation).filter(
            Consultation.id == body.consultation_id,
            Consultation.doctor_id == doctor_profile.id
        ).first()
        if not consultation:
            raise HTTPException(status_code=404, detail="问诊记录不存在")
    # 校验药品有效性
    product_ids = [item.product_id for item in body.items]
    products = db.query(ShopProduct).filter(ShopProduct.id.in_(product_ids), ShopProduct.status == True).all()
    product_map = {p.id: p for p in products}
    for item in body.items:
        if item.product_id not in product_map:
            raise HTTPException(status_code=404, detail=f"药品 {item.product_id} 不存在或已下架")
    prescription = Prescription(
        patient_id=body.patient_id,
        doctor_id=doctor_profile.id,
        consultation_id=body.consultation_id,
        diagnosis=body.diagnosis,
        notes=body.notes,
        valid_until=body.valid_until,
        status="approved"
    )
    db.add(prescription)
    db.flush()
    for item in body.items:
        db.add(PrescriptionItem(
            prescription_id=prescription.id,
            product_id=item.product_id,
            dosage=item.dosage,
            frequency=item.frequency,
            duration=item.duration
        ))
    db.commit()
    db.refresh(prescription)
    return _build_prescription_detail(prescription)


@router.get("/prescriptions", response_model=List[PrescriptionOut])
def list_prescriptions(
    authorization: str = Header(None),
    patient_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """获取医生开具的处方列表"""
    _, doctor_profile = get_current_doctor(authorization, db)
    query = db.query(Prescription).filter(Prescription.doctor_id == doctor_profile.id)
    if patient_id:
        query = query.filter(Prescription.patient_id == patient_id)
    if status:
        query = query.filter(Prescription.status == status)
    items = query.order_by(desc(Prescription.created_at)).offset(offset).limit(limit).all()
    return [_build_prescription_detail(item) for item in items]


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionOut)
def get_prescription_detail(prescription_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取处方详情"""
    _, doctor_profile = get_current_doctor(authorization, db)
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.doctor_id == doctor_profile.id
    ).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="处方不存在")
    return _build_prescription_detail(prescription)


@router.put("/prescriptions/{prescription_id}", response_model=PrescriptionOut)
def update_prescription(prescription_id: int, body: PrescriptionUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """更新处方（状态、诊断、备注、有效期）"""
    _, doctor_profile = get_current_doctor(authorization, db)
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.doctor_id == doctor_profile.id
    ).first()
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
    return _build_prescription_detail(prescription)


@router.put("/password")
def doctor_change_password(body: PasswordChange, authorization: str = Header(None), db: Session = Depends(get_db)):
    """医生修改密码"""
    user, _ = get_current_doctor(authorization, db)
    if not verify_password(body.old_password, user.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少 6 位")
    user.password = hash_password(body.new_password)
    user.updated_at = datetime.now()
    db.commit()
    return {"message": "密码修改成功"}


@router.put("/consultations/{consultation_id}/start", response_model=ConsultationOut)
def start_consultation(consultation_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """开始问诊（视频通话开始）"""
    _, doctor_profile = get_current_doctor(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.doctor_id == doctor_profile.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="问诊记录不存在")
    if consultation.status not in ("pending", "confirmed"):
        raise HTTPException(status_code=400, detail="当前状态不允许开始问诊")
    consultation.status = "ongoing"
    consultation.start_time = datetime.now()
    consultation.updated_at = datetime.now()
    db.commit()
    db.refresh(consultation)
    return consultation


@router.post("/video-calls/{consultation_id}/join", response_model=VideoCallOut)
def join_video_call(consultation_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, doctor_profile = get_current_doctor(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.doctor_id == doctor_profile.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="视频问诊不存在")
    if consultation.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="当前问诊已结束")
    if consultation.status != "ongoing":
        consultation.status = "ongoing"
    if not consultation.start_time:
        consultation.start_time = datetime.now()
    consultation.updated_at = datetime.now()
    db.commit()
    db.refresh(consultation)
    patient = db.query(PatientProfile).filter(PatientProfile.id == consultation.patient_id).first()
    return build_video_call_payload(consultation, "doctor", doctor_profile, patient)


@router.get("/video-calls/{consultation_id}", response_model=VideoCallOut)
def get_video_call(consultation_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, doctor_profile = get_current_doctor(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.doctor_id == doctor_profile.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="视频问诊不存在")
    patient = db.query(PatientProfile).filter(PatientProfile.id == consultation.patient_id).first()
    return build_video_call_payload(consultation, "doctor", doctor_profile, patient)


@router.put("/video-calls/{consultation_id}/end", response_model=VideoCallOut)
def end_video_call(consultation_id: int, body: Optional[VideoCallEnd] = None, authorization: str = Header(None), db: Session = Depends(get_db)):
    _, doctor_profile = get_current_doctor(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.doctor_id == doctor_profile.id
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
    patient = db.query(PatientProfile).filter(PatientProfile.id == consultation.patient_id).first()
    return build_video_call_payload(consultation, "doctor", doctor_profile, patient)


@router.put("/consultations/{consultation_id}/end", response_model=ConsultationOut)
def end_consultation(consultation_id: int, body: ConsultationUpdate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """结束问诊：写入诊断、治疗方案，状态置为 completed"""
    _, doctor_profile = get_current_doctor(authorization, db)
    consultation = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.doctor_id == doctor_profile.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="问诊记录不存在")
    if consultation.status not in ("ongoing", "confirmed", "pending"):
        raise HTTPException(status_code=400, detail="当前状态不允许结束问诊")
    data = body.model_dump(exclude_unset=True)
    for key in ("diagnosis", "treatment_plan", "prescription", "notes"):
        if key in data:
            setattr(consultation, key, data[key])
    consultation.status = "completed"
    consultation.end_time = datetime.now()
    consultation.updated_at = datetime.now()
    db.commit()
    db.refresh(consultation)
    return consultation


@router.post("/patients/{patient_id}/sign", response_model=PatientDetail)
def sign_patient(patient_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """医生签约患者（建立医患关系）"""
    _, doctor_profile = get_current_doctor(authorization, db)
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    if patient.doctor_id and patient.doctor_id != doctor_profile.id:
        raise HTTPException(status_code=400, detail="患者已签约其他医生")
    patient.doctor_id = doctor_profile.id
    patient.updated_at = datetime.now()
    db.commit()
    db.refresh(patient)
    return build_patient_detail(db, patient)


@router.delete("/patients/{patient_id}/sign")
def unsign_patient(patient_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    """解除签约关系"""
    _, doctor_profile = get_current_doctor(authorization, db)
    patient = db.query(PatientProfile).filter(
        PatientProfile.id == patient_id,
        PatientProfile.doctor_id == doctor_profile.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="未找到签约关系")
    patient.doctor_id = None
    patient.updated_at = datetime.now()
    db.commit()
    return {"message": "已解除签约"}


@router.get("/news", response_model=List[NewsOut])
def list_news(limit: int = Query(10, description="返回数据条数限制"), db: Session = Depends(get_db)):
    """获取新闻动态列表"""
    return db.query(News).filter(News.published == True).order_by(desc(News.published_at)).limit(limit).all()


@router.get("/news/{news_id}", response_model=NewsOut)
def get_news_detail(news_id: int, db: Session = Depends(get_db)):
    """获取新闻详情"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    news.views += 1
    db.commit()
    return news
