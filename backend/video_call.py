import os

from config import settings


def _join_stream_url(base_url, stream_id):
    if not base_url:
        return None
    separator = '' if base_url.endswith('/') else '/'
    return base_url + separator + stream_id


def _join_api_url(base_url, path):
    if not base_url:
        return None
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url + path


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

    webrtc_push_base_url = (os.getenv('VIDEO_PUSH_BASE_URL') or settings.video_push_base_url or '').strip()
    webrtc_play_base_url = (os.getenv('VIDEO_PLAY_BASE_URL') or settings.video_play_base_url or '').strip()
    rtmp_push_base_url = (os.getenv('VIDEO_RTMP_PUSH_BASE_URL') or settings.video_rtmp_push_base_url or '').strip()
    rtmp_play_base_url = (os.getenv('VIDEO_RTMP_PLAY_BASE_URL') or settings.video_rtmp_play_base_url or '').strip()
    rtc_api_base_url = (os.getenv('VIDEO_RTC_API_BASE_URL') or settings.video_rtc_api_base_url or '').strip()
    if role == 'patient':
        push_base_url = rtmp_push_base_url or webrtc_push_base_url
        play_base_url = rtmp_play_base_url or webrtc_play_base_url
    else:
        push_base_url = webrtc_push_base_url
        play_base_url = webrtc_play_base_url
    local_push_url = _join_stream_url(push_base_url, local_stream_id)
    remote_play_url = _join_stream_url(play_base_url, remote_stream_id)
    rtc_publish_api = _join_api_url(rtc_api_base_url, '/rtc/v1/publish/') if role == 'doctor' else None
    rtc_play_api = _join_api_url(rtc_api_base_url, '/rtc/v1/play/') if role == 'doctor' else None

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
        'rtc_publish_api': rtc_publish_api,
        'rtc_play_api': rtc_play_api,
        'stream_ready': bool(local_push_url and remote_play_url)
    }
