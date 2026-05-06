"""
工具函数
"""
import hashlib
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from models import MeasurementType

# JWT配置
SECRET_KEY = "your-secret-key-change-in-production"  # 生产环境需要更换
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天


def hash_password(password: str) -> str:
    """
    密码哈希
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT Token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """
    解码JWT Token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user_id(authorization: str):
    """
    从Authorization header获取当前用户ID
    用于FastAPI的Depends依赖注入
    """
    from fastapi import HTTPException
    
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证格式错误")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    return payload.get("user_id")


def analyze_blood_pressure(systolic: float, diastolic: float) -> Dict:
    """
    血压AI分析
    根据中国高血压防治指南
    """
    risk_level = "normal"
    suggestion = ""
    
    if systolic < 120 and diastolic < 80:
        risk_level = "normal"
        suggestion = "血压正常，请继续保持健康的生活方式，低盐饮食，适量运动。"
    elif systolic < 130 and diastolic < 85:
        risk_level = "normal"
        suggestion = "血压正常偏高，建议注意饮食，减少盐分摄入，增加运动。"
    elif systolic < 140 and diastolic < 90:
        risk_level = "warning"
        suggestion = "血压偏高（高血压前期），建议：1.减少盐分摄入；2.控制体重；3.戒烟限酒；4.定期监测血压。如持续偏高，请咨询医生。"
    elif systolic < 160 and diastolic < 100:
        risk_level = "warning"
        suggestion = "血压偏高（1级高血压），建议尽快联系医生，可能需要药物治疗。同时注意：1.低盐低脂饮食；2.避免劳累和情绪激动；3.每天监测血压。"
    else:
        risk_level = "danger"
        suggestion = "血压过高（2级或以上高血压），请立即联系医生或就医！注意：1.避免剧烈活动；2.保持情绪稳定；3.按医嘱服药；4.密切监测血压变化。"
    
    return {
        "risk_level": risk_level,
        "suggestion": suggestion
    }


def analyze_blood_sugar(value: float, measurement_time: str = "fasting") -> Dict:
    """
    血糖AI分析
    measurement_time: fasting(空腹), postprandial(餐后2小时), random(随机)
    """
    risk_level = "normal"
    suggestion = ""
    
    if measurement_time == "fasting":
        if value < 6.1:
            risk_level = "normal"
            suggestion = "空腹血糖正常，请继续保持健康饮食和生活习惯。"
        elif value < 7.0:
            risk_level = "warning"
            suggestion = "空腹血糖升高（糖尿病前期），建议：1.控制饮食，减少精制糖和碳水化合物；2.增加运动；3.控制体重；4.定期监测血糖。"
        else:
            risk_level = "danger"
            suggestion = "空腹血糖过高，可能为糖尿病，请尽快就医进行全面检查。注意：1.严格控制饮食；2.规律服药；3.每天监测血糖。"
    elif measurement_time == "postprandial":
        if value < 7.8:
            risk_level = "normal"
            suggestion = "餐后血糖正常，请继续保持。"
        elif value < 11.1:
            risk_level = "warning"
            suggestion = "餐后血糖升高，建议控制饮食，减少碳水化合物摄入，增加运动，定期监测。"
        else:
            risk_level = "danger"
            suggestion = "餐后血糖过高，请尽快就医。注意饮食控制和按时服药。"
    else:  # random
        if value < 11.1:
            risk_level = "normal"
            suggestion = "随机血糖正常范围。"
        else:
            risk_level = "danger"
            suggestion = "随机血糖过高，建议尽快就医检查。"
    
    return {
        "risk_level": risk_level,
        "suggestion": suggestion
    }


def analyze_heart_rate(value: float) -> Dict:
    """
    心率AI分析
    """
    risk_level = "normal"
    suggestion = ""
    
    if 60 <= value <= 100:
        risk_level = "normal"
        suggestion = "心率正常，请继续保持。"
    elif value < 60:
        risk_level = "warning"
        suggestion = "心率偏低（心动过缓），如无不适可能是运动员心脏，如有头晕、乏力等症状，请咨询医生。"
    elif value <= 120:
        risk_level = "warning"
        suggestion = "心率偏快，可能与情绪、运动、咖啡因等有关。如持续偏快或伴有不适，请就医。"
    else:
        risk_level = "danger"
        suggestion = "心率过快，请注意休息，如伴有胸闷、气短等症状，请立即就医。"
    
    return {
        "risk_level": risk_level,
        "suggestion": suggestion
    }


def ai_analyze_measurement(measurement_type: MeasurementType, value1: float, value2: Optional[float] = None) -> Dict:
    """
    统一的AI分析入口
    """
    if measurement_type == MeasurementType.BLOOD_PRESSURE:
        if value2 is None:
            return {"risk_level": "normal", "suggestion": "请同时提供收缩压和舒张压数据。"}
        return analyze_blood_pressure(value1, value2)
    elif measurement_type == MeasurementType.BLOOD_SUGAR:
        return analyze_blood_sugar(value1)
    elif measurement_type == MeasurementType.HEART_RATE:
        return analyze_heart_rate(value1)
    elif measurement_type == MeasurementType.WEIGHT:
        return {"risk_level": "normal", "suggestion": "体重已记录，请保持规律监测。"}
    elif measurement_type == MeasurementType.TEMPERATURE:
        if value1 < 36.0:
            return {"risk_level": "warning", "suggestion": "体温偏低，注意保暖。"}
        elif value1 <= 37.3:
            return {"risk_level": "normal", "suggestion": "体温正常。"}
        elif value1 <= 38.0:
            return {"risk_level": "warning", "suggestion": "体温略高，注意休息，多喝水。"}
        else:
            return {"risk_level": "danger", "suggestion": "发热，请及时就医。"}
    
    return {"risk_level": "normal", "suggestion": "数据已记录。"}


def format_chronic_diseases(diseases: list) -> str:
    """
    格式化慢性病数据为JSON字符串
    """
    return json.dumps(diseases, ensure_ascii=False)


def parse_chronic_diseases(diseases_str: Optional[str]) -> list:
    """
    解析慢性病JSON字符串
    """
    if not diseases_str:
        return []
    try:
        return json.loads(diseases_str)
    except:
        return []


def format_reminder_times(times: list) -> str:
    """
    格式化提醒时间为JSON字符串
    """
    return json.dumps(times, ensure_ascii=False)


def parse_reminder_times(times_str: Optional[str]) -> list:
    """
    解析提醒时间JSON字符串
    """
    if not times_str:
        return []
    try:
        return json.loads(times_str)
    except:
        return []
