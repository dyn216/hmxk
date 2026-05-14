"""
AI 健康助手服务（基于小米 MiMo，OpenAI 兼容协议）
- 多轮对话：从 ai_chat_messages 表中读取历史，调用 MiMo 后保存
- 测量后建议：根据本次测量+最近 N 天历史+档案+用药生成结构化建议
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc

from config import settings
from models import (
    PatientProfile, Measurement, MeasurementType, Medication, AiChatMessage
)
from utils import parse_chronic_diseases

try:
    from openai import OpenAI  # type: ignore
    _OPENAI_AVAILABLE = True
except Exception:  # pragma: no cover - 依赖未安装时不致于崩溃整个后端
    OpenAI = None  # type: ignore
    _OPENAI_AVAILABLE = False


# 中文展示用：测量类型 -> 名称、单位、合理生理范围
MEASUREMENT_META = {
    MeasurementType.BLOOD_PRESSURE: ("血压", "mmHg"),
    MeasurementType.BLOOD_SUGAR: ("血糖", "mmol/L"),
    MeasurementType.HEART_RATE: ("心率", "bpm"),
    MeasurementType.WEIGHT: ("体重", "kg"),
    MeasurementType.TEMPERATURE: ("体温", "℃"),
}


SYSTEM_PROMPT_DOCTOR = (
    "你是「惠民携康」小程序的 AI 健康助手，由小米 MiMo 大模型提供能力，"
    "面向慢性病患者提供日常健康咨询、生活方式建议和用药/测量提示。"
    "请遵守：\n"
    "1. 回答使用简体中文，语气专业、温和、易懂；\n"
    "2. 严格基于用户提供的健康档案、用药情况和测量数据进行个性化回答，"
    "不臆造数据；如信息不足请主动询问；\n"
    "3. 不能替代医生面诊，不开具处方剂量；如发现高血压危象、低血糖昏迷、"
    "持续胸痛、严重心律失常等危急情况，必须明确建议立即就医或拨打急救电话；\n"
    "4. 对药物使用只给一般性教育性提醒，具体调整须遵医嘱；\n"
    "5. 回答简洁，控制在 300 字以内，必要时分点列出。\n"
    "回答末尾不要重复添加免责声明，前端会统一展示。"
)


SYSTEM_PROMPT_MEASUREMENT = (
    "你是「惠民携康」小程序的 AI 健康助手。请根据用户档案、用药、最近一周历史测量"
    "和本次智能手表上传的最新生命体征，给出一段不超过 220 字的中文健康建议。"
    "要求：\n"
    "1. 先用 1 句话总结本次测量是否在合理范围；\n"
    "2. 再给出 2-4 条针对性的生活方式或监测建议（饮食、运动、休息、复测、用药提醒等）；\n"
    "3. 严格基于真实数据，不臆造；缺失字段请忽略，不要凭空补全；\n"
    "4. 同时按以下 JSON 格式输出结构化字段，便于前端解析：\n"
    "{\n"
    "  \"summary\": \"本次测量整体评价，一句话\",\n"
    "  \"risk_level\": \"normal|warning|danger\",\n"
    "  \"abnormal\": true/false,\n"
    "  \"need_doctor\": true/false,\n"
    "  \"advice\": [\"建议1\", \"建议2\"]\n"
    "}\n"
    "请把 JSON 放在回答的最后，并使用 ```json 代码块包裹。"
)


# ---------------- 公共：上下文构建 ----------------

def _format_measurement(m: Measurement) -> str:
    name, unit = MEASUREMENT_META.get(m.type, (str(m.type), ""))
    if m.type == MeasurementType.BLOOD_PRESSURE:
        value = f"{int(m.value1)}/{int(m.value2) if m.value2 is not None else '-'}"
    else:
        value = f"{m.value1:g}"
    when = m.measured_at.strftime("%Y-%m-%d %H:%M") if m.measured_at else ""
    risk = f"，风险:{m.risk_level}" if m.risk_level else ""
    return f"- {when} {name} {value} {unit}{risk}"


def build_health_context(db: Session, profile: PatientProfile, days: int = 7) -> str:
    """根据患者档案+最近 days 天测量+用药+慢病史/过敏史构建上下文文本"""
    user = profile.user
    parts: List[str] = []
    parts.append("【患者档案】")
    name = user.name if user else "用户"
    parts.append(f"- 姓名:{name}")
    if profile.gender:
        parts.append(f"- 性别:{profile.gender}")
    if profile.age:
        parts.append(f"- 年龄:{profile.age}")
    if profile.height:
        parts.append(f"- 身高:{profile.height}cm")
    if profile.weight:
        parts.append(f"- 体重:{profile.weight}kg")

    diseases = parse_chronic_diseases(profile.chronic_diseases)
    if diseases:
        parts.append("- 慢性病史:" + "、".join(str(d) for d in diseases))
    if profile.allergies:
        parts.append(f"- 过敏史:{profile.allergies}")

    # 用药
    meds = db.query(Medication).filter(Medication.patient_id == profile.id).all()
    if meds:
        parts.append("\n【当前用药】")
        for med in meds[:20]:
            line = f"- {med.drug_name}"
            if med.dosage:
                line += f" {med.dosage}"
            if med.frequency:
                line += f" {med.frequency}"
            parts.append(line)

    # 最近 N 天测量记录
    since = datetime.now() - timedelta(days=days)
    measurements = (
        db.query(Measurement)
        .filter(Measurement.patient_id == profile.id, Measurement.measured_at >= since)
        .order_by(desc(Measurement.measured_at))
        .limit(60)
        .all()
    )
    if measurements:
        parts.append(f"\n【最近{days}天测量记录（按时间倒序，最多 60 条）】")
        for m in measurements:
            parts.append(_format_measurement(m))
    else:
        parts.append(f"\n【最近{days}天测量记录】暂无记录")

    return "\n".join(parts)


# ---------------- 公共：MiMo 调用 ----------------

class AiServiceError(Exception):
    pass


def _get_client():
    if not _OPENAI_AVAILABLE:
        raise AiServiceError("服务端缺少 openai 依赖，请安装 openai>=1.0")
    if not settings.mimo_api_key:
        raise AiServiceError("AI 服务未配置 MIMO_API_KEY")
    return OpenAI(
        api_key=settings.mimo_api_key,
        base_url=settings.mimo_base_url,
        timeout=settings.mimo_timeout,
    )


def _chat_completion(messages: List[Dict[str, str]]) -> str:
    client = _get_client()
    try:
        completion = client.chat.completions.create(
            model=settings.mimo_model,
            messages=messages,
            max_completion_tokens=settings.mimo_max_completion_tokens,
            temperature=settings.mimo_temperature,
            top_p=0.95,
            stream=False,
        )
    except Exception as exc:  # 网络/鉴权错误统一封装
        raise AiServiceError(f"AI 服务调用失败：{exc}")
    try:
        return completion.choices[0].message.content or ""
    except Exception:
        raise AiServiceError("AI 返回数据格式异常")


# ---------------- AI 医生对话 ----------------

def load_chat_history(
    db: Session, patient_id: int, limit: Optional[int] = None
) -> List[AiChatMessage]:
    query = (
        db.query(AiChatMessage)
        .filter(AiChatMessage.patient_id == patient_id)
        .order_by(AiChatMessage.created_at.asc(), AiChatMessage.id.asc())
    )
    rows = query.all()
    if limit and len(rows) > limit:
        rows = rows[-limit:]
    return rows


def chat_with_ai_doctor(db: Session, profile: PatientProfile, user_text: str) -> Tuple[str, AiChatMessage, AiChatMessage]:
    """处理一次用户提问，返回 (assistant_text, user_msg, assistant_msg)"""
    user_text = (user_text or "").strip()
    if not user_text:
        raise AiServiceError("请输入要咨询的内容")

    # 持久化用户消息
    user_msg = AiChatMessage(patient_id=profile.id, role="user", content=user_text)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 拉取最近上下文
    history = load_chat_history(db, profile.id, limit=settings.mimo_history_window)

    # 拼装 messages：system(角色) + system(健康上下文) + 历史
    health_context = build_health_context(db, profile, days=settings.mimo_measurement_days)
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT_DOCTOR},
        {"role": "system", "content": "以下为该患者的最新健康资料，仅你可见，请据此个性化回答：\n" + health_context},
    ]
    for msg in history:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})

    try:
        reply = _chat_completion(messages)
    except AiServiceError:
        # 失败时回滚刚保存的 user 消息以避免出现“只问没答”的孤儿记录
        db.delete(user_msg)
        db.commit()
        raise

    reply = reply.strip() or "抱歉，AI 暂时未能给出建议，请稍后再试。"
    assistant_msg = AiChatMessage(patient_id=profile.id, role="assistant", content=reply)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return reply, user_msg, assistant_msg


def clear_chat_history(db: Session, patient_id: int) -> int:
    count = (
        db.query(AiChatMessage)
        .filter(AiChatMessage.patient_id == patient_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return count


# ---------------- 测量后建议 ----------------

def _extract_json_block(text: str) -> Optional[Dict]:
    if not text:
        return None
    # 优先匹配 ```json ... ```
    import re
    matches = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not matches:
        # 退化：找第一个 {...}
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            matches = [m.group(0)]
    for raw in matches:
        try:
            return json.loads(raw)
        except Exception:
            continue
    return None


def _strip_json_block(text: str) -> str:
    import re
    return re.sub(r"```json[\s\S]*?```", "", text or "").strip()


def measurement_advice(
    db: Session,
    profile: PatientProfile,
    measurement_payload: Dict,
) -> Dict:
    """根据本次测量与历史数据生成 AI 建议

    measurement_payload 结构示例（device 页打包）:
    {
      "source": "smart_watch",
      "measured_at": "2026-05-14T12:00:00Z",
      "items": [
        {"type": "bp", "systolic": 142, "diastolic": 95},
        {"type": "hr", "heart_rate": 102},
        {"type": "spo2", "spo2": 95}
      ]
    }
    """
    payload = dict(measurement_payload or {})
    payload.setdefault("measured_at", datetime.now().isoformat())

    health_context = build_health_context(db, profile, days=settings.mimo_measurement_days)

    user_message = (
        "以下是本次刚刚通过智能手表上传的生命体征：\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n\n请结合下方健康资料给出建议。\n"
        + health_context
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_MEASUREMENT},
        {"role": "user", "content": user_message},
    ]
    reply = _chat_completion(messages)

    structured = _extract_json_block(reply) or {}
    advice_text = _strip_json_block(reply)

    risk_level = (structured.get("risk_level") or "").lower()
    if risk_level not in ("normal", "warning", "danger"):
        risk_level = "warning" if structured.get("abnormal") else "normal"
    abnormal = bool(structured.get("abnormal", risk_level != "normal"))
    need_doctor = bool(structured.get("need_doctor", risk_level == "danger"))

    advice_list = structured.get("advice")
    if not isinstance(advice_list, list):
        advice_list = []
    advice_list = [str(item).strip() for item in advice_list if str(item).strip()]

    summary = structured.get("summary") or ""
    if not summary:
        summary = (advice_text.split("\n", 1)[0] if advice_text else "")[:120]

    return {
        "summary": summary.strip(),
        "advice_text": advice_text or summary,
        "advice_list": advice_list,
        "risk_level": risk_level,
        "abnormal": abnormal,
        "need_doctor": need_doctor,
        "model": settings.mimo_model,
        "generated_at": datetime.now().isoformat(),
    }
