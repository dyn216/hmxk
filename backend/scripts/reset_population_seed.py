import argparse
import hashlib
import json
import random
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

OLD_MEASUREMENT_DEVICE_ID = "MONITOR-SEED-001"
POPULATION_DEVICE_ID = "POP-SEED-001"
POPULATION_PHONE_PREFIX = "17166"
DEFAULT_PATIENT_COUNT = 600
DEFAULT_TOTAL_MEASUREMENTS = 5422
DEFAULT_MIN_MEASUREMENTS = 5
DEFAULT_MAX_MEASUREMENTS = 10

SURNAMES = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐费廉岑薛雷贺倪汤"
MALE_NAMES = ["建国", "国华", "志强", "建军", "文斌", "德明", "志刚", "永强", "伟民", "长青", "明远", "振华"]
FEMALE_NAMES = ["秀英", "桂兰", "玉珍", "丽华", "淑芬", "美玲", "慧芳", "春梅", "秀兰", "静怡", "雅琴", "素珍"]
DISTRICTS = ["惠城区", "惠阳区", "仲恺高新区", "博罗县", "惠东县", "龙门县", "大亚湾区"]
STREETS = ["江北街道", "桥东街道", "河南岸街道", "淡水街道", "秋长街道", "罗阳街道", "平山街道", "永汉镇"]
DISEASE_GROUPS = [
    ["高血压"],
    ["糖尿病"],
    ["高血压", "糖尿病"],
    ["冠心病"],
    ["高血压", "冠心病"],
    ["慢性病随访"],
]
MEASUREMENT_TYPES = ("BLOOD_PRESSURE", "HEART_RATE", "BLOOD_SUGAR", "TEMPERATURE", "WEIGHT")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def format_datetime(value):
    return value.strftime("%Y-%m-%d %H:%M:%S.%f")


def risk_for(measurement_type, value1, value2):
    if measurement_type == "BLOOD_PRESSURE":
        if value1 >= 160 or (value2 is not None and value2 >= 100):
            return "danger", "血压明显偏高，请及时复测并联系医生。"
        if value1 >= 140 or (value2 is not None and value2 >= 90):
            return "warning", "血压偏高，建议低盐饮食并规律监测。"
        if value1 < 90 or (value2 is not None and value2 < 60):
            return "warning", "血压偏低，如有头晕乏力请及时就医。"
        return "normal", "血压正常，请继续保持健康生活方式。"
    if measurement_type == "BLOOD_SUGAR":
        if value1 >= 11.1:
            return "danger", "血糖明显偏高，请及时复测并联系医生。"
        if value1 >= 7.0:
            return "warning", "血糖偏高，建议控制饮食并规律复测。"
        if value1 < 3.9:
            return "warning", "血糖偏低，请注意补充糖分并观察症状。"
        return "normal", "血糖处于参考范围，请继续规律监测。"
    if measurement_type == "HEART_RATE":
        if value1 > 120 or value1 < 45:
            return "danger", "心率异常明显，请休息后复测，必要时及时就医。"
        if value1 > 100 or value1 < 60:
            return "warning", "心率略有异常，建议保持休息并继续观察。"
        return "normal", "心率正常，请继续保持规律监测。"
    if measurement_type == "TEMPERATURE":
        if value1 >= 38.0 or value1 < 35.5:
            return "danger", "体温异常，请及时复测并关注身体状况。"
        if value1 > 37.3 or value1 < 36.0:
            return "warning", "体温略有波动，请注意休息并继续观察。"
        return "normal", "体温正常。"
    return "normal", "数据已记录，请保持规律监测。"


def patient_measurement_type(rng, diseases):
    if "高血压" in diseases and rng.random() < 0.46:
        return "BLOOD_PRESSURE"
    if "糖尿病" in diseases and rng.random() < 0.38:
        return "BLOOD_SUGAR"
    return rng.choices(MEASUREMENT_TYPES, weights=(38, 26, 16, 10, 10), k=1)[0]


def generate_values(rng, age, diseases, measurement_type, index):
    age_factor = max(0, age - 50) / 30
    wave = rng.uniform(-1, 1)
    has_hypertension = "高血压" in diseases
    has_diabetes = "糖尿病" in diseases
    if measurement_type == "BLOOD_PRESSURE":
        systolic_base = 122 + age_factor * 8 + (10 if has_hypertension else 0)
        diastolic_base = 76 + age_factor * 4 + (5 if has_hypertension else 0)
        if index % 29 == 0:
            systolic_base += rng.randint(10, 18)
            diastolic_base += rng.randint(3, 8)
        return int(max(96, min(168, round(systolic_base + wave * 7 + rng.randint(-6, 6))))), int(max(58, min(104, round(diastolic_base + wave * 4 + rng.randint(-4, 4)))))
    if measurement_type == "BLOOD_SUGAR":
        base = 5.6 + (1.2 if has_diabetes else 0) + age_factor * 0.4
        if index % 31 == 0:
            base += rng.uniform(0.8, 1.6)
        return round(max(3.8, min(11.6, base + rng.uniform(-0.6, 0.9))), 1), None
    if measurement_type == "HEART_RATE":
        base = 74 + age_factor * 2
        if index % 37 == 0:
            base += rng.randint(15, 26)
        return int(max(48, min(128, round(base + rng.randint(-10, 12))))), None
    if measurement_type == "TEMPERATURE":
        base = 36.5 + rng.uniform(-0.25, 0.35)
        if index % 53 == 0:
            base += rng.uniform(0.4, 0.8)
        return round(max(35.8, min(38.2, base)), 1), None
    base = 61 + age_factor * 2 + rng.uniform(-5, 8)
    return round(max(45, min(92, base)), 1), None


def row_signature(row):
    return (
        row[0],
        row[1],
        round(float(row[2]), 2),
        None if row[3] is None else round(float(row[3]), 2),
    )


def duplicate_stats(rows, window_size=100):
    if not rows:
        return 0, []
    values = []
    for start in range(len(rows)):
        window = rows[start:start + window_size]
        if len(window) < min(window_size, len(rows)) and start != 0:
            break
        signatures = [row_signature(row) for row in window]
        values.append(len(signatures) - len(set(signatures)))
    return max(values), values


def validate_measurement_rows(rows):
    issues = []
    for index, row in enumerate(rows, 1):
        measurement_type = row[1]
        value1 = float(row[2])
        value2 = None if row[3] is None else float(row[3])
        if measurement_type == "BLOOD_PRESSURE":
            if value2 is None or not (90 <= value1 <= 180 and 55 <= value2 <= 110 and value1 > value2):
                issues.append((index, row))
        elif measurement_type == "BLOOD_SUGAR":
            if value2 is not None or not (3.8 <= value1 <= 11.6):
                issues.append((index, row))
        elif measurement_type == "HEART_RATE":
            if value2 is not None or not (45 <= value1 <= 130):
                issues.append((index, row))
        elif measurement_type == "TEMPERATURE":
            if value2 is not None or not (35.8 <= value1 <= 38.2):
                issues.append((index, row))
        elif measurement_type == "WEIGHT":
            if value2 is not None or not (45 <= value1 <= 92):
                issues.append((index, row))
        else:
            issues.append((index, row))
    return issues


def build_record_counts(patient_count, min_measurements, max_measurements, total_measurements, rng):
    if total_measurements is None:
        return [rng.randint(min_measurements, max_measurements) for _ in range(patient_count)]
    min_total = patient_count * min_measurements
    max_total = patient_count * max_measurements
    if total_measurements < min_total or total_measurements > max_total:
        raise RuntimeError(f"总条数必须在 {min_total}-{max_total} 之间")
    counts = [min_measurements] * patient_count
    remaining = total_measurements - min_total
    order = list(range(patient_count))
    rng.shuffle(order)
    while remaining > 0:
        progressed = False
        for index in order:
            capacity = max_measurements - counts[index]
            if capacity <= 0:
                continue
            step = min(remaining, capacity, rng.randint(1, capacity))
            counts[index] += step
            remaining -= step
            progressed = True
            if remaining == 0:
                break
        if not progressed:
            raise RuntimeError("无法分配监测条数")
    return counts


def fetch_doctor_ids(connection):
    rows = connection.execute("select id from doctor_profiles order by id").fetchall()
    return [row[0] for row in rows]


def existing_population_patient_ids(connection):
    rows = connection.execute(
        """
        select pp.id
        from patient_profiles pp
        join users u on u.id = pp.user_id
        where u.phone like ?
        """,
        (f"{POPULATION_PHONE_PREFIX}%",),
    ).fetchall()
    return [row[0] for row in rows]


def existing_population_user_ids(connection):
    rows = connection.execute("select id from users where phone like ?", (f"{POPULATION_PHONE_PREFIX}%",)).fetchall()
    return [row[0] for row in rows]


def delete_population_seed(connection):
    patient_ids = existing_population_patient_ids(connection)
    user_ids = existing_population_user_ids(connection)
    stats = {}
    stats["old_measurements"] = connection.execute(
        "delete from measurements where device_id = ?",
        (OLD_MEASUREMENT_DEVICE_ID,),
    ).rowcount
    stats["population_device_measurements"] = connection.execute(
        "delete from measurements where device_id = ?",
        (POPULATION_DEVICE_ID,),
    ).rowcount
    if patient_ids:
        placeholders = ",".join("?" for _ in patient_ids)
        for table in ("measurements", "patient_addresses", "guardians", "medications", "follow_ups", "devices"):
            stats[table] = connection.execute(
                f"delete from {table} where patient_id in ({placeholders})",
                patient_ids,
            ).rowcount
        stats["patient_profiles"] = connection.execute(
            f"delete from patient_profiles where id in ({placeholders})",
            patient_ids,
        ).rowcount
    else:
        for table in ("measurements", "patient_addresses", "guardians", "medications", "follow_ups", "devices", "patient_profiles"):
            stats[table] = 0
    if user_ids:
        placeholders = ",".join("?" for _ in user_ids)
        stats["users"] = connection.execute(f"delete from users where id in ({placeholders})", user_ids).rowcount
    else:
        stats["users"] = 0
    return stats


def build_patient(index, rng, doctor_ids):
    gender = "男" if rng.random() < 0.48 else "女"
    surname = rng.choice(SURNAMES)
    given_name = rng.choice(MALE_NAMES if gender == "男" else FEMALE_NAMES)
    name = f"{surname}{given_name}"
    age = rng.randint(45, 82)
    diseases = rng.choice(DISEASE_GROUPS)
    now = datetime.now().replace(microsecond=0)
    created_at = now - timedelta(days=rng.randint(1, 180), hours=rng.randint(0, 23))
    phone = f"{POPULATION_PHONE_PREFIX}{index + 1:06d}"
    height = round(rng.uniform(154, 178) if gender == "女" else rng.uniform(162, 182), 1)
    weight = round(rng.uniform(48, 78) if gender == "女" else rng.uniform(58, 88), 1)
    address = f"广东省惠州市{rng.choice(DISTRICTS)}{rng.choice(STREETS)}健康社区{rng.randint(1, 36)}栋{rng.randint(101, 2404)}室"
    doctor_id = doctor_ids[index % len(doctor_ids)] if doctor_ids else None
    user_row = (
        phone,
        hash_password("patient123"),
        name,
        "https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0",
        "PATIENT",
        1,
        format_datetime(created_at),
        format_datetime(created_at),
        None,
    )
    profile = {
        "age": age,
        "gender": gender,
        "address": address,
        "height": height,
        "weight": weight,
        "chronic_diseases": json.dumps(diseases, ensure_ascii=False),
        "allergies": json.dumps([] if rng.random() < 0.85 else ["青霉素"], ensure_ascii=False),
        "emergency_contact": f"{surname}{rng.choice(['家属', '子女', '配偶'])}",
        "emergency_phone": f"17288{index + 1:06d}",
        "doctor_id": doctor_id,
        "created_at": created_at,
    }
    return user_row, profile, diseases


def insert_population(connection, patient_count, min_measurements, max_measurements, total_measurements, seed):
    rng = random.Random(seed)
    doctor_ids = fetch_doctor_ids(connection)
    record_counts = build_record_counts(patient_count, min_measurements, max_measurements, total_measurements, rng)
    user_sql = """
    insert into users
    (phone, password, name, avatar, role, status, created_at, updated_at, last_login)
    values (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    profile_sql = """
    insert into patient_profiles
    (user_id, age, gender, address, emergency_contact, emergency_phone, height, weight, chronic_diseases, allergies, doctor_id, created_at, updated_at)
    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    address_sql = """
    insert into patient_addresses
    (patient_id, name, phone, address, is_default, created_at, updated_at)
    values (?, ?, ?, ?, ?, ?, ?)
    """
    measurement_sql = """
    insert into measurements
    (patient_id, type, value1, value2, measured_at, device_id, notes, risk_level, ai_suggestion, created_at)
    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    measurement_rows = []
    measurement_counter = Counter()
    created_patients = []
    now = datetime.now().replace(microsecond=0)
    global_index = 0
    for index in range(patient_count):
        user_row, profile, diseases = build_patient(index, rng, doctor_ids)
        cursor = connection.execute(user_sql, user_row)
        user_id = cursor.lastrowid
        profile_created = format_datetime(profile["created_at"])
        cursor = connection.execute(
            profile_sql,
            (
                user_id,
                profile["age"],
                profile["gender"],
                profile["address"],
                profile["emergency_contact"],
                profile["emergency_phone"],
                profile["height"],
                profile["weight"],
                profile["chronic_diseases"],
                profile["allergies"],
                profile["doctor_id"],
                profile_created,
                profile_created,
            ),
        )
        patient_id = cursor.lastrowid
        connection.execute(
            address_sql,
            (patient_id, user_row[2], user_row[0], profile["address"], 1, profile_created, profile_created),
        )
        created_patients.append((patient_id, user_row[0], user_row[2]))
        record_count = record_counts[index]
        measurement_counter[record_count] += 1
        used_signatures = []
        for local_index in range(record_count):
            if used_signatures and global_index >= 17 and global_index % 17 == 0:
                measurement_type, value1, value2 = rng.choice(used_signatures)
            else:
                for attempt in range(100):
                    measurement_type = patient_measurement_type(rng, diseases)
                    value1, value2 = generate_values(rng, profile["age"], diseases, measurement_type, index * 17 + local_index + attempt)
                    signature = (measurement_type, value1, value2)
                    if signature not in used_signatures:
                        break
            used_signatures.append((measurement_type, value1, value2))
            measured_at = now - timedelta(days=rng.randint(0, 45), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
            created_at = measured_at + timedelta(minutes=rng.randint(1, 90))
            risk_level, suggestion = risk_for(measurement_type, value1, value2)
            measurement_rows.append(
                (
                    patient_id,
                    measurement_type,
                    float(value1),
                    None if value2 is None else float(value2),
                    format_datetime(measured_at),
                    POPULATION_DEVICE_ID,
                    "批量生成患者少量监测数据",
                    risk_level,
                    suggestion,
                    format_datetime(created_at),
                )
            )
            global_index += 1
    max_duplicates, _ = duplicate_stats(measurement_rows)
    if max_duplicates > 6:
        raise RuntimeError(f"重复率校验失败：任意100条内最多重复 {max_duplicates} 条")
    invalid_rows = validate_measurement_rows(measurement_rows)
    if invalid_rows:
        raise RuntimeError(f"数值校验失败：发现 {len(invalid_rows)} 条异常数据")
    connection.executemany(measurement_sql, measurement_rows)
    return created_patients, measurement_rows, measurement_counter


def snapshot(connection):
    return {
        "users": connection.execute("select count(*) from users").fetchone()[0],
        "patients": connection.execute("select count(*) from patient_profiles").fetchone()[0],
        "measurements": connection.execute("select count(*) from measurements").fetchone()[0],
        "old_seed_measurements": connection.execute("select count(*) from measurements where device_id = ?", (OLD_MEASUREMENT_DEVICE_ID,)).fetchone()[0],
        "population_users": connection.execute("select count(*) from users where phone like ?", (f"{POPULATION_PHONE_PREFIX}%",)).fetchone()[0],
        "population_measurements": connection.execute("select count(*) from measurements where device_id = ?", (POPULATION_DEVICE_ID,)).fetchone()[0],
    }


def print_plan(before, cleanup_stats, patient_count, min_measurements, max_measurements, total_measurements, seed):
    print("当前数据库:", before)
    print("将清理:", cleanup_stats)
    print("将生成患者账号:", patient_count)
    print("每个患者监测条数:", f"{min_measurements}-{max_measurements}")
    print("目标监测总数:", total_measurements if total_measurements is not None else "随机")
    print("手机号前缀:", POPULATION_PHONE_PREFIX)
    print("默认密码: patient123")
    print("随机种子:", seed)


def print_result(before, after, created_patients, measurement_rows, measurement_counter):
    type_counter = Counter(row[1] for row in measurement_rows)
    risk_counter = Counter(row[7] for row in measurement_rows)
    patient_counts = Counter(row[0] for row in measurement_rows)
    max_duplicates, duplicate_windows = duplicate_stats(measurement_rows)
    invalid_rows = validate_measurement_rows(measurement_rows)
    min_count = min(patient_counts.values()) if patient_counts else 0
    max_count = max(patient_counts.values()) if patient_counts else 0
    print("插入前:", before)
    print("插入后:", after)
    print("新增患者账号:", len(created_patients))
    print("新增监测数据:", len(measurement_rows))
    print("每人监测条数范围:", f"{min_count}-{max_count}")
    print("每人条数分布:", dict(sorted(measurement_counter.items())))
    print("类型分布:", dict(sorted(type_counter.items())))
    print("风险分布:", dict(sorted(risk_counter.items())))
    print("任意100条内最多重复:", max_duplicates)
    print("前10个100条窗口重复数:", duplicate_windows[:10])
    print("数值校验异常条数:", len(invalid_rows))
    print("前5个账号:", created_patients[:5])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(Path(__file__).resolve().parents[1] / "chronic_disease.db"))
    parser.add_argument("--patients", type=int, default=DEFAULT_PATIENT_COUNT)
    parser.add_argument("--total-measurements", type=int, default=DEFAULT_TOTAL_MEASUREMENTS)
    parser.add_argument("--min-measurements", type=int, default=DEFAULT_MIN_MEASUREMENTS)
    parser.add_argument("--max-measurements", type=int, default=DEFAULT_MAX_MEASUREMENTS)
    parser.add_argument("--seed", type=int, default=52010)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    if args.patients < 500:
        raise SystemExit("patients 必须至少为 500")
    if args.min_measurements < 1 or args.max_measurements < args.min_measurements:
        raise SystemExit("监测条数范围不合法")
    if args.max_measurements > 10:
        raise SystemExit("max-measurements 不能超过 10")

    db_path = Path(args.db).resolve()
    if not db_path.exists():
        raise SystemExit(f"数据库不存在：{db_path}")

    connection = sqlite3.connect(db_path)
    try:
        before = snapshot(connection)
        connection.execute("begin")
        cleanup_stats = delete_population_seed(connection)
        created_patients, measurement_rows, measurement_counter = insert_population(
            connection,
            args.patients,
            args.min_measurements,
            args.max_measurements,
            args.total_measurements,
            args.seed,
        )
        if not args.commit:
            print_plan(before, cleanup_stats, args.patients, args.min_measurements, args.max_measurements, args.total_measurements, args.seed)
            print_result(before, snapshot(connection), created_patients, measurement_rows, measurement_counter)
            connection.rollback()
            print("当前为 dry-run，未写入数据库。加 --commit 才会执行清理和插入。")
            return
        connection.commit()
        after = snapshot(connection)
        print_result(before, after, created_patients, measurement_rows, measurement_counter)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
