<template>
  <div v-if="visible" class="video-call-mask">
    <section class="video-call-card">
      <header class="video-call-head">
        <div>
          <p class="eyebrow">VIDEO CONSULTATION</p>
          <h3>视频问诊房间 <small>{{ room?.room_id || '—' }}</small></h3>
          <p>{{ statusText }}</p>
        </div>
        <button class="ghost-btn" @click="closePanel">关闭</button>
      </header>

      <div class="video-call-grid">
        <div class="video-stage remote">
          <video ref="remoteVideo" autoplay playsinline controls></video>
          <div v-if="!remoteReady" class="video-empty">
            <strong>患者画面</strong>
            <span>{{ room?.remote_play_url || '等待患者推流' }}</span>
          </div>
        </div>
        <div class="video-stage local">
          <video ref="localVideo" autoplay playsinline muted></video>
          <div v-if="!localReady" class="video-empty">
            <strong>本端画面</strong>
            <span>{{ room?.local_push_url || '等待本端推流配置' }}</span>
          </div>
        </div>
      </div>

      <div class="video-call-meta">
        <span>问诊 #{{ room?.consultation_id || '—' }}</span>
        <span>患者：{{ room?.patient_name || room?.patient_id || '—' }}</span>
        <span>状态：{{ room?.status || '—' }}</span>
      </div>

      <div class="video-call-actions">
        <button class="primary-btn" :disabled="connecting || publishing" @click="startMedia">开启摄像头/麦克风</button>
        <button class="secondary-btn" :disabled="connecting || !canPlay" @click="playRemote">播放患者画面</button>
        <button class="secondary-btn" :disabled="!localStream" @click="toggleAudio">{{ audioEnabled ? '关闭麦克风' : '开启麦克风' }}</button>
        <button class="secondary-btn" :disabled="!localStream" @click="toggleVideo">{{ videoEnabled ? '关闭摄像头' : '开启摄像头' }}</button>
        <button class="danger-btn" @click="endCall">结束问诊</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  room: { type: Object, default: null },
  signalRtc: { type: Function, default: null }
});

const emit = defineEmits(['close', 'end']);

const localVideo = ref(null);
const remoteVideo = ref(null);
const localStream = ref(null);
const publishPeer = ref(null);
const playPeer = ref(null);
const connecting = ref(false);
const publishing = ref(false);
const localReady = ref(false);
const remoteReady = ref(false);
const statusText = ref('房间已建立，准备连接音视频');
const audioEnabled = ref(true);
const videoEnabled = ref(true);

const canPlay = computed(() => Boolean(props.room?.remote_play_url && props.room?.rtc_play_api));

watch(() => props.visible, value => {
  if (!value) stopRtc();
});

async function startMedia() {
  if (!props.room?.local_push_url || !props.room?.rtc_publish_api) {
    statusText.value = '未配置本端推流地址或 SRS RTC API';
    return;
  }
  connecting.value = true;
  statusText.value = '正在请求摄像头和麦克风权限';
  try {
    await nextTick();
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localStream.value = stream;
    audioEnabled.value = stream.getAudioTracks().some(track => track.enabled);
    videoEnabled.value = stream.getVideoTracks().some(track => track.enabled);
    if (localVideo.value) {
      localVideo.value.srcObject = stream;
      await localVideo.value.play().catch(() => {});
    }
    localReady.value = true;
    await publishLocal(stream);
    if (canPlay.value) await playRemote();
  } catch (err) {
    if (err?.name === 'NotAllowedError') {
      statusText.value = '摄像头/麦克风权限被浏览器禁止，请点击地址栏锁图标允许权限后刷新页面';
    } else if (!navigator.mediaDevices?.getUserMedia) {
      statusText.value = '当前页面不是安全上下文，请使用 localhost 或 HTTPS 打开医生端';
    } else {
      statusText.value = err?.message || '无法开启摄像头/麦克风';
    }
  } finally {
    connecting.value = false;
  }
}

async function publishLocal(stream) {
  publishing.value = true;
  statusText.value = '正在推送医生端音视频';
  try {
    closePeer(publishPeer.value);
    const peer = createPeer();
    stream.getTracks().forEach(track => peer.addTrack(track, stream));
    publishPeer.value = peer;
    const offer = await peer.createOffer();
    await peer.setLocalDescription(offer);
    await waitForIceGathering(peer);
    const answer = await requestSrs('publish', props.room.rtc_publish_api, props.room.local_push_url, peer.localDescription.sdp);
    await peer.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp: answer.sdp }));
    statusText.value = '医生端音视频已推送';
  } catch (err) {
    statusText.value = err?.message || '医生端推流失败';
  } finally {
    publishing.value = false;
  }
}

async function playRemote() {
  if (!canPlay.value) {
    statusText.value = '未配置患者画面拉流地址或 SRS RTC API';
    return;
  }
  statusText.value = '正在拉取患者音视频';
  try {
    closePeer(playPeer.value);
    const peer = createPeer();
    peer.addTransceiver('audio', { direction: 'recvonly' });
    peer.addTransceiver('video', { direction: 'recvonly' });
    peer.ontrack = event => {
      if (remoteVideo.value && event.streams && event.streams[0]) {
        remoteVideo.value.srcObject = event.streams[0];
        remoteVideo.value.play().catch(() => {});
        remoteReady.value = true;
      }
    };
    playPeer.value = peer;
    const offer = await peer.createOffer();
    await peer.setLocalDescription(offer);
    await waitForIceGathering(peer);
    const answer = await requestSrs('play', props.room.rtc_play_api, props.room.remote_play_url, peer.localDescription.sdp);
    await peer.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp: answer.sdp }));
    statusText.value = '视频问诊音视频已连接';
  } catch (err) {
    statusText.value = err?.message || '患者音视频暂不可用';
  }
}

function createPeer() {
  return new RTCPeerConnection({
    bundlePolicy: 'max-bundle',
    rtcpMuxPolicy: 'require',
    iceServers: []
  });
}

async function waitForIceGathering(peer) {
  if (peer.iceGatheringState === 'complete') return;
  await new Promise(resolve => {
    const timer = window.setTimeout(resolve, 3000);
    function onChange() {
      if (peer.iceGatheringState === 'complete') {
        window.clearTimeout(timer);
        peer.removeEventListener('icegatheringstatechange', onChange);
        resolve();
      }
    }
    peer.addEventListener('icegatheringstatechange', onChange);
  });
}

async function requestSrs(action, api, streamurl, sdp) {
  const body = { api, streamurl, clientip: null, sdp };
  if (props.signalRtc) {
    return props.signalRtc(action, body);
  }
  const response = await fetch(api, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  if (!response.ok || payload.code !== 0) {
    throw new Error(payload?.msg || payload?.message || 'SRS RTC 接口调用失败');
  }
  return payload;
}

function toggleAudio() {
  if (!localStream.value) return;
  audioEnabled.value = !audioEnabled.value;
  localStream.value.getAudioTracks().forEach(track => {
    track.enabled = audioEnabled.value;
  });
}

function toggleVideo() {
  if (!localStream.value) return;
  videoEnabled.value = !videoEnabled.value;
  localStream.value.getVideoTracks().forEach(track => {
    track.enabled = videoEnabled.value;
  });
}

function endCall() {
  stopRtc();
  emit('end', props.room);
}

function closePanel() {
  stopRtc();
  emit('close');
}

function stopRtc() {
  closePeer(publishPeer.value);
  closePeer(playPeer.value);
  publishPeer.value = null;
  playPeer.value = null;
  if (localStream.value) {
    localStream.value.getTracks().forEach(track => track.stop());
  }
  localStream.value = null;
  if (localVideo.value) localVideo.value.srcObject = null;
  if (remoteVideo.value) remoteVideo.value.srcObject = null;
  localReady.value = false;
  remoteReady.value = false;
  connecting.value = false;
  publishing.value = false;
  statusText.value = '房间已建立，准备连接音视频';
}

function closePeer(peer) {
  if (peer) peer.close();
}

onBeforeUnmount(stopRtc);
</script>
