import os

from config import settings


def _join_stream_url(base_url, stream_id):
    if not base_url:
        return None
    separator = '' if base_url.endswith('/') else '/'
    return base_url + separator + stream_id


def _patient_name(patient):
    if patient and patient.user:
        return patient.user.name
    return ''


def _doctor_name(doctor):
    if doctor and doctor.user:
        return doctor.user.name
    return ''


def build_video_call_payload(consultation, role, doctor, patient):
    room_id = 'consultation_' + str(consultation.id)
    patient_stream_id = room_id + '_patient'
    doctor_stream_id = room_id + '_doctor'
    if role == 'doctor':
        local_stream_id = doctor_stream_id
        remote_stream_id = patient_stream_id
    else:
        local_stream_id = patient_stream_id
        remote_stream_id = doctor_stream_id

    push_base_url = (os.getenv('VIDEO_PUSH_BASE_URL') or settings.video_push_base_url or '').strip()
    play_base_url = (os.getenv('VIDEO_PLAY_BASE_URL') or settings.video_play_base_url or '').strip()
    local_push_url = _join_stream_url(push_base_url, local_stream_id)
    remote_play_url = _join_stream_url(play_base_url, remote_stream_id)

    return {
        'consultation_id': consultation.id,
        'room_id': room_id,
        'role': role,
        'status': consultation.status,
        'doctor_id': doctor.id if doctor else consultation.doctor_id,
        'doctor_name': _doctor_name(doctor),
        'department': doctor.department if doctor else '',
        'patient_id': patient.id if patient else consultation.patient_id,
        'patient_name': _patient_name(patient),
        'start_time': consultation.start_time,
        'end_time': consultation.end_time,
        'local_stream_id': local_stream_id,
        'remote_stream_id': remote_stream_id,
        'local_push_url': local_push_url,
        'remote_play_url': remote_play_url,
        'stream_ready': bool(local_push_url and remote_play_url)
    }
