"""
数据库初始化脚本
创建所有表并添加测试数据
"""
from database import engine, SessionLocal, Base
from models import (
    User, PatientProfile, DoctorProfile, AdminProfile,
    Measurement, Medication, Guardian, Device,
    Message, Consultation, FollowUp, News, SystemLog,
    PatientAddress, ShopProduct, Prescription, PrescriptionItem,
    UserRole, MeasurementType
)
from utils import hash_password
from datetime import datetime, timedelta
import random


def init_database():
    """
    初始化数据库，创建所有表
    """
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")


def create_test_data():
    """
    创建测试数据
    """
    db = SessionLocal()
    
    try:
        print("\n添加测试数据...")
        
        # 1. 创建管理员
        print("创建管理员...")
        admin_user = User(
            phone="13800000000",
            password=hash_password("admin123"),
            name="系统管理员",
            avatar="https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0",
            role=UserRole.ADMIN,
            last_login=datetime.now()
        )
        db.add(admin_user)
        db.flush()
        
        admin_profile = AdminProfile(
            user_id=admin_user.id,
            institution="广东省惠州市人民医院",
            permissions='{"all": true}'
        )
        db.add(admin_profile)
        
        # 2. 创建医生
        print("创建医生...")
        doctors_data = [
            {
                "phone": "13800000001",
                "name": "张医生",
                "department": "心血管内科",
                "title": "副主任医师",
                "hospital": "惠州市人民医院",
                "license_number": "110440123456789"
            },
            {
                "phone": "13800000002",
                "name": "李医生",
                "department": "内分泌科",
                "title": "主治医师",
                "hospital": "惠州市人民医院",
                "license_number": "110440123456790"
            }
        ]
        
        doctors = []
        for doctor_data in doctors_data:
            doctor_user = User(
                phone=doctor_data["phone"],
                password=hash_password("doctor123"),
                name=doctor_data["name"],
                avatar="https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0",
                role=UserRole.DOCTOR,
                last_login=datetime.now()
            )
            db.add(doctor_user)
            db.flush()
            
            doctor_profile = DoctorProfile(
                user_id=doctor_user.id,
                department=doctor_data["department"],
                title=doctor_data["title"],
                hospital=doctor_data["hospital"],
                license_number=doctor_data["license_number"],
                introduction=f"{doctor_data['name']}，{doctor_data['title']}，从事临床工作15年。"
            )
            db.add(doctor_profile)
            db.flush()
            doctors.append(doctor_profile)
        
        # 3. 创建患者
        print("创建患者...")
        patients_data = [
            {
                "phone": "13900000001",
                "name": "王大爷",
                "age": 65,
                "gender": "男",
                "address": "广东省惠州市惠城区XX街道",
                "chronic_diseases": '["高血压", "糖尿病"]'
            },
            {
                "phone": "13900000002",
                "name": "张阿姨",
                "age": 58,
                "gender": "女",
                "address": "广东省惠州市惠城区YY街道",
                "chronic_diseases": '["高血压"]'
            },
            {
                "phone": "13900000003",
                "name": "李大伯",
                "age": 72,
                "gender": "男",
                "address": "广东省惠州市惠阳区ZZ街道",
                "chronic_diseases": '["高血压", "冠心病"]'
            }
        ]
        
        patients = []
        for i, patient_data in enumerate(patients_data):
            patient_user = User(
                phone=patient_data["phone"],
                password=hash_password("patient123"),
                name=patient_data["name"],
                avatar="https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0",
                role=UserRole.PATIENT,
                last_login=datetime.now()
            )
            db.add(patient_user)
            db.flush()
            
            patient_profile = PatientProfile(
                user_id=patient_user.id,
                age=patient_data["age"],
                gender=patient_data["gender"],
                address=patient_data["address"],
                height=168.0 + i * 5,
                weight=70.0 + i * 3,
                chronic_diseases=patient_data["chronic_diseases"],
                emergency_contact="家属" + str(i+1),
                emergency_phone="139000000" + str(i+10),
                doctor_id=doctors[i % len(doctors)].id
            )
            db.add(patient_profile)
            db.flush()
            patients.append(patient_profile)

            address = PatientAddress(
                patient_id=patient_profile.id,
                name=patient_user.name,
                phone=patient_user.phone,
                address=patient_data["address"],
                is_default=True
            )
            db.add(address)
        
        # 4. 创建监测数据
        print("创建监测数据...")
        for patient in patients:
            # 最近7天的血压数据
            for day in range(7):
                measurement_date = datetime.now() - timedelta(days=day)
                
                # 血压数据（每天2-3次）
                for _ in range(random.randint(2, 3)):
                    systolic = random.randint(120, 155)
                    diastolic = random.randint(75, 95)
                    
                    measurement = Measurement(
                        patient_id=patient.id,
                        type=MeasurementType.BLOOD_PRESSURE,
                        value1=systolic,
                        value2=diastolic,
                        measured_at=measurement_date + timedelta(hours=random.randint(6, 20)),
                        device_id="BP001",
                        risk_level="warning" if systolic > 140 else "normal"
                    )
                    db.add(measurement)
                
                # 血糖数据（部分患者）
                if "糖尿病" in patient.chronic_diseases:
                    blood_sugar = random.uniform(5.5, 8.5)
                    measurement = Measurement(
                        patient_id=patient.id,
                        type=MeasurementType.BLOOD_SUGAR,
                        value1=blood_sugar,
                        measured_at=measurement_date + timedelta(hours=7),
                        device_id="BG001",
                        risk_level="warning" if blood_sugar > 7.0 else "normal"
                    )
                    db.add(measurement)
        
        # 5. 创建用药记录
        print("创建用药记录...")
        for patient in patients:
            if "高血压" in patient.chronic_diseases:
                medication = Medication(
                    patient_id=patient.id,
                    drug_name="缬沙坦胶囊",
                    dosage="80mg",
                    frequency="每天1次",
                    start_date=datetime.now() - timedelta(days=30),
                    reminder_times='["08:00"]',
                    reminder_enabled=True,
                    notes="早晨服用"
                )
                db.add(medication)
            
            if "糖尿病" in patient.chronic_diseases:
                medication = Medication(
                    patient_id=patient.id,
                    drug_name="二甲双胍片",
                    dosage="500mg",
                    frequency="每天2次",
                    start_date=datetime.now() - timedelta(days=60),
                    reminder_times='["08:00", "18:00"]',
                    reminder_enabled=True,
                    notes="餐后服用"
                )
                db.add(medication)

        print("创建商城商品...")
        products_data = [
            {
                "name": "缬沙坦胶囊",
                "specification": "80mg*7粒",
                "price": 28.8,
                "category": "hypertension",
                "manufacturer": "惠州制药",
                "approval_number": "国药准字H20230001",
                "description": "用于高血压患者日常用药管理",
                "usage": "遵医嘱服用",
                "precautions": "孕妇及哺乳期妇女慎用",
                "unit": "盒",
                "stock": 120,
                "is_prescription": True
            },
            {
                "name": "二甲双胍片",
                "specification": "500mg*30片",
                "price": 19.9,
                "category": "diabetes",
                "manufacturer": "惠州制药",
                "approval_number": "国药准字H20230002",
                "description": "用于糖尿病患者血糖控制",
                "usage": "餐后服用",
                "precautions": "肾功能不全者慎用",
                "unit": "盒",
                "stock": 100,
                "is_prescription": True
            },
            {
                "name": "电子血压计袖带",
                "specification": "通用成人款",
                "price": 49.0,
                "category": "device",
                "manufacturer": "惠州健康设备",
                "approval_number": "粤械备20230001",
                "description": "适配常见电子血压计",
                "usage": "连接血压计后使用",
                "precautions": "请按说明书佩戴",
                "unit": "个",
                "stock": 80,
                "is_prescription": False
            },
            {
                "name": "血糖试纸",
                "specification": "50片/盒",
                "price": 69.0,
                "category": "device",
                "manufacturer": "惠州健康设备",
                "approval_number": "粤械备20230002",
                "description": "用于配套血糖仪检测",
                "usage": "配合血糖仪使用",
                "precautions": "开封后请密封保存",
                "unit": "盒",
                "stock": 90,
                "is_prescription": False
            }
        ]
        products = []
        for product_data in products_data:
            product = ShopProduct(**product_data)
            db.add(product)
            db.flush()
            products.append(product)

        print("创建处方...")
        prescription_products = [product for product in products if product.is_prescription]
        for i, patient in enumerate(patients):
            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=patient.doctor_id,
                diagnosis="高血压" if "高血压" in patient.chronic_diseases else "慢病管理",
                notes="按医嘱用药，定期复诊",
                valid_until=datetime.now() + timedelta(days=30),
                status="approved"
            )
            db.add(prescription)
            db.flush()
            for product in prescription_products[:1 + (i % len(prescription_products))]:
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    product_id=product.id,
                    dosage="1片" if "二甲双胍" in product.name else "1粒",
                    frequency="每日2次" if "二甲双胍" in product.name else "每日1次",
                    duration="30天"
                )
                db.add(item)
        
        # 6. 创建监护人
        print("创建监护人...")
        for i, patient in enumerate(patients):
            guardian = Guardian(
                patient_id=patient.id,
                name=f"患者{i+1}的子女",
                phone=f"139000001{i}0",
                relation_type="子女",
                can_view_data=True,
                can_receive_alerts=True
            )
            db.add(guardian)
        
        # 7. 创建设备
        print("创建设备...")
        device_types = [
            {"device_id": "BP00100001", "device_name": "智能血压计", "device_type": "血压计", "model": "iHealth BP5"},
            {"device_id": "BG00100001", "device_name": "智能血糖仪", "device_type": "血糖仪", "model": "三诺安稳+"},
        ]
        
        for i, patient in enumerate(patients):
            device_data = device_types[i % len(device_types)]
            device = Device(
                device_id=device_data["device_id"] + str(i),
                device_name=device_data["device_name"],
                device_type=device_data["device_type"],
                model=device_data["model"],
                patient_id=patient.id,
                status="online",
                battery_level=random.randint(50, 100),
                last_sync=datetime.now() - timedelta(hours=random.randint(1, 12))
            )
            db.add(device)
        
        # 8. 创建新闻动态
        print("创建新闻动态...")
        news_list = [
            {
                "title": "新增高血压患者管理指南",
                "content": "根据最新的《中国高血压防治指南2023》，我们更新了患者管理流程...",
                "category": "指南",
                "published": True,
                "published_at": datetime.now() - timedelta(days=1)
            },
            {
                "title": "系统将在今晚进行维护",
                "content": "为提升系统性能，我们将于今晚22:00-24:00进行系统维护...",
                "category": "通知",
                "published": True,
                "published_at": datetime.now() - timedelta(days=2)
            },
            {
                "title": "新版健康报告模板已上线",
                "content": "全新的健康报告模板，提供更详细的数据分析和健康建议...",
                "category": "公告",
                "published": True,
                "published_at": datetime.now() - timedelta(days=3)
            }
        ]
        
        for news_data in news_list:
            news = News(
                title=news_data["title"],
                content=news_data["content"],
                category=news_data["category"],
                author_id=admin_user.id,
                published=news_data["published"],
                published_at=news_data["published_at"],
                views=random.randint(10, 100)
            )
            db.add(news)
        
        # 9. 创建随访计划
        print("创建随访计划...")
        for i, patient in enumerate(patients):
            follow_up = FollowUp(
                patient_id=patient.id,
                doctor_id=doctors[i % len(doctors)].id,
                scheduled_date=datetime.now() + timedelta(days=random.randint(1, 7)),
                follow_up_type="phone",
                notes="定期随访"
            )
            db.add(follow_up)
        
        db.commit()
        print("\n测试数据创建完成！")
        
        print("\n=== 测试账号信息 ===")
        print("管理员账号：13800000000 / admin123")
        print("医生账号1：13800000001 / doctor123")
        print("医生账号2：13800000002 / doctor123")
        print("患者账号1：13900000001 / patient123")
        print("患者账号2：13900000002 / patient123")
        print("患者账号3：13900000003 / patient123")
        print("=====================")
        
    except Exception as e:
        print(f"创建测试数据时出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # 初始化数据库
    init_database()
    
    # 询问是否创建测试数据
    response = input("\n是否创建测试数据? (y/n): ")
    if response.lower() == 'y':
        create_test_data()
    
    print("\n数据库初始化完成！")
