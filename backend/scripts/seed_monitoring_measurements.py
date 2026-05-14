import argparse
import math
import random
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

MEASUREMENT_TYPES = ("HEART_RATE", "BLOOD_PRESSURE", "BLOOD_SUGAR", "TEMPERATURE", "WEIGHT")
TYPE_WEIGHTS = (42, 30, 13, 9, 6)


def parse_patient_ids(value):
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def format_datetime(value):
    return value.strftime("%Y-%m-%d %H:%M:%S.%f")


def risk_for(measurement_type, value1, value2):
    if measurement_type == "BLOOD_PRESSURE":
        if value1 >= 160 or (value2 is not None and value2 >= 100):
            return "danger", "血压明显偏高，请及时复测并联系医生。"
        if value1 >= 140 or (value2 is not None and value2 >= 90):
            return "warning", "血压偏高，建议规律监测并注意低盐饮食。"
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


def choose_type(rng):
    return rng.choices(MEASUREMENT_TYPES, weights=TYPE_WEIGHTS, k=1)[0]


def generate_values(rng, patient_id, measurement_type, index):
    day_phase = math.sin(index / 19.0 + patient_id)
    week_phase = math.sin(index / 73.0 + patient_id * 0.7)
    if measurement_type == "HEART_RATE":
        value = int(round(76 + day_phase * 9 + week_phase * 5 + rng.randint(-8, 8)))
        if index % 89 == 0:
            value += rng.randint(16, 28)
        return max(48, min(132, value)), None
    if measurement_type == "BLOOD_PRESSURE":
        systolic = int(round(126 + patient_id * 2 + day_phase * 8 + week_phase * 5 + rng.randint(-7, 7)))
        diastolic = int(round(78 + patient_id + day_phase * 4 + week_phase * 3 + rng.randint(-5, 5)))
        if index % 61 == 0:
            systolic += rng.randint(12, 22)
            diastolic += rng.randint(4, 10)
        return max(96, min(165, systolic)), max(58, min(102, diastolic))
    if measurement_type == "BLOOD_SUGAR":
        value = round(5.8 + day_phase * 0.7 + week_phase * 0.4 + rng.uniform(-0.5, 0.8), 1)
        if index % 83 == 0:
            value += round(rng.uniform(1.1, 2.0), 1)
        return max(3.8, min(10.8, value)), None
    if measurement_type == "TEMPERATURE":
        value = round(36.5 + day_phase * 0.25 + rng.uniform(-0.15, 0.25), 1)
        if index % 127 == 0:
            value += round(rng.uniform(0.5, 0.9), 1)
        return max(35.8, min(38.1, value)), None
    value = round(63.0 + patient_id * 2.7 + week_phase * 0.8 + rng.uniform(-0.6, 0.6), 1)
    return max(45.0, min(92.0, value)), None


def row_signature(row):
    return (row[0], row[1], round(float(row[2]), 2), None if row[3] is None else round(float(row[3]), 2))


def duplicate_stats(rows, window_size=100):
    if not rows:
        return 0, []
    values = []
    for start in range(0, len(rows)):
        window = rows[start:start + window_size]
        if len(window) < min(window_size, len(rows)) and start != 0:
            break
        signatures = [row_signature(row) for row in window]
        duplicate_count = len(signatures) - len(set(signatures))
        values.append(duplicate_count)
    return max(values), values


def build_rows(patient_ids, count, seed):
    rng = random.Random(seed)
    now = datetime.now().replace(microsecond=0)
    start = now - timedelta(days=180)
    interval_seconds = max(60, int((180 * 24 * 60 * 60) / max(count, 1)))
    rows = []
    recent_signatures = []
    recent_counts = Counter()
    for index in range(count):
        measured_at = start + timedelta(seconds=index * interval_seconds + rng.randint(-240, 240))
        created_at = measured_at + timedelta(seconds=rng.randint(1, 180))
        source_candidates = [
            row for row in rows[max(0, index - 16):max(0, index - 7)]
            if recent_counts[row_signature(row)] == 1
        ]
        use_duplicate = index >= 17 and index % 17 == 0 and source_candidates
        if use_duplicate:
            source = rng.choice(source_candidates)
            patient_id, measurement_type, value1, value2 = source[0], source[1], source[2], source[3]
        else:
            for attempt in range(1000):
                patient_id = patient_ids[(index + attempt) % len(patient_ids)]
                measurement_type = choose_type(rng)
                value1, value2 = generate_values(rng, patient_id, measurement_type, index + attempt * 23 + rng.randint(0, 17))
                candidate = (
                    patient_id,
                    measurement_type,
                    round(float(value1), 2),
                    None if value2 is None else round(float(value2), 2),
                )
                if recent_counts[candidate] == 0:
                    break
            else:
                raise RuntimeError("无法生成满足重复率要求的数据")
        risk_level, suggestion = risk_for(measurement_type, value1, value2)
        row = (
            patient_id,
            measurement_type,
            float(value1),
            None if value2 is None else float(value2),
            format_datetime(measured_at),
            "MONITOR-SEED-001",
            "批量生成测试监测数据",
            risk_level,
            suggestion,
            format_datetime(created_at),
        )
        rows.append(row)
        signature = row_signature(row)
        recent_signatures.append(signature)
        recent_counts[signature] += 1
        if len(recent_signatures) > 99:
            old_signature = recent_signatures.pop(0)
            recent_counts[old_signature] -= 1
            if recent_counts[old_signature] <= 0:
                del recent_counts[old_signature]
    max_duplicates, _ = duplicate_stats(rows)
    if max_duplicates > 6:
        raise RuntimeError(f"重复率校验失败：任意100条内最多重复 {max_duplicates} 条")
    return rows


def fetch_patient_ids(connection, requested_ids):
    cursor = connection.cursor()
    if requested_ids:
        placeholders = ",".join("?" for _ in requested_ids)
        rows = cursor.execute(f"select id from patient_profiles where id in ({placeholders}) order by id", requested_ids).fetchall()
        found_ids = [row[0] for row in rows]
        missing = sorted(set(requested_ids) - set(found_ids))
        if missing:
            raise RuntimeError(f"患者不存在：{missing}")
        return found_ids
    rows = cursor.execute("select id from patient_profiles order by id").fetchall()
    patient_ids = [row[0] for row in rows]
    if not patient_ids:
        raise RuntimeError("数据库中没有患者档案")
    return patient_ids


def print_summary(rows, patient_ids):
    patient_counter = Counter(row[0] for row in rows)
    type_counter = Counter(row[1] for row in rows)
    max_duplicates, values = duplicate_stats(rows)
    print("目标患者:", ",".join(str(item) for item in patient_ids))
    print("生成条数:", len(rows))
    print("患者分布:", dict(sorted(patient_counter.items())))
    print("类型分布:", dict(sorted(type_counter.items())))
    print("任意100条内最多重复:", max_duplicates)
    print("前10个100条窗口重复数:", values[:10])
    print("最后测量时间:", rows[-1][4] if rows else "")


def insert_rows(connection, rows):
    sql = """
    insert into measurements
    (patient_id, type, value1, value2, measured_at, device_id, notes, risk_level, ai_suggestion, created_at)
    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor = connection.cursor()
    cursor.executemany(sql, rows)
    connection.commit()
    return cursor.rowcount


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(Path(__file__).resolve().parents[1] / "chronic_disease.db"))
    parser.add_argument("--count", type=int, default=5422)
    parser.add_argument("--patient-ids", default="")
    parser.add_argument("--seed", type=int, default=5422)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    if not db_path.exists():
        raise SystemExit(f"数据库不存在：{db_path}")
    if args.count <= 0:
        raise SystemExit("count 必须大于 0")

    connection = sqlite3.connect(db_path)
    try:
        patient_ids = fetch_patient_ids(connection, parse_patient_ids(args.patient_ids))
        rows = build_rows(patient_ids, args.count, args.seed)
        print_summary(rows, patient_ids)
        if not args.commit:
            print("当前为 dry-run，未写入数据库。加 --commit 才会插入。")
            return
        before = connection.execute("select count(*) from measurements").fetchone()[0]
        inserted = insert_rows(connection, rows)
        after = connection.execute("select count(*) from measurements").fetchone()[0]
        print("插入条数:", inserted)
        print("插入前总数:", before)
        print("插入后总数:", after)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
