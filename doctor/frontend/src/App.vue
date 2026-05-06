<template>
  <LoginScreen
    v-if="!isLoggedIn"
    :module="moduleName"
    :current="current"
    :error="error"
    :loading="loading"
    @submit="login"
    @switch-module="redirectToModule"
  />

  <section v-else class="layout">
    <AppSidebar
      :current="current"
      :user-info="userInfo"
      :page="page"
      @navigate="setPage"
    />
    <main class="main">
      <AppTopBar :title="pageTitle" :crumbs="crumbs">
        <button class="ghost-btn" @click="redirectToModule('admin')">前往管理端</button>
        <button class="danger-btn" @click="logout">退出登录</button>
      </AppTopBar>

      <div v-if="loading" class="card loading">载入数据中</div>
      <div v-else-if="error" class="card error">{{ error }}</div>

      <template v-else>
        <template v-if="page === 'dashboard'">
          <StatGrid :items="stats" />
          <section class="card quick-actions reveal" data-delay="3">
            <h3>常用动作</h3>
            <p>诊室节奏所需的常规动作集中此处，避免在导航之间来回切换。</p>
            <div class="row-actions">
              <button class="primary-btn" @click="createConsultation()">+ 新增问诊</button>
              <button class="primary-btn" @click="createPrescription()">+ 新增处方</button>
              <button class="secondary-btn" @click="sendPatientMessage()">发送消息</button>
              <button class="secondary-btn" @click="createFollowUp()">新建随访</button>
              <button class="secondary-btn" @click="setPage('profile')">编辑个人资料</button>
            </div>
          </section>
        </template>

        <template v-else-if="page === 'profile'">
          <Toolbar :can-create="false">
            <button class="primary-btn" @click="editProfile">编辑个人资料</button>
          </Toolbar>
          <ProfilePanel
            :items="profileItems"
            :name="profileName"
            :role="profileRole"
          />
        </template>

        <template v-else>
          <Toolbar
            :can-search="canSearch"
            :can-filter-status="canFilterStatus"
            :search="filters.search"
            :status="filters.status"
            :can-create="canCreate"
            :create-label="createLabel"
            @update:search="filters.search = $event"
            @update:status="filters.status = $event"
            @query="loadPage"
            @create="createRecord"
          >
            <template v-if="page === 'patients'">
              <button class="secondary-btn" @click="createPrescription()">按 ID 开处方</button>
              <button class="secondary-btn" @click="sendPatientMessage()">按 ID 发消息</button>
              <button class="secondary-btn" @click="createFollowUp()">按 ID 建随访</button>
            </template>
          </Toolbar>
          <DataTable
            :rows="rows"
            :columns="columns"
            :show-operations="showOperations"
            :row-actions="rowActions"
          />
        </template>
      </template>
    </main>
  </section>

  <FormModal
    :visible="modal.visible"
    :title="modal.title"
    :meta="modal.meta"
    :description="modal.description"
    :fields="modal.fields"
    :model="modal.model"
    :show-submit="Boolean(modal.submit)"
    @update:field="updateModalField"
    @submit="submitModal"
    @close="closeModal"
  />
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { modules } from './config.js';
import {
  createApi,
  buildQuery,
  compactData,
  displayText,
  formatDate,
  toInputDateTime,
  normalizeFormData
} from './composables/useApi.js';
import LoginScreen from './components/LoginScreen.vue';
import AppSidebar from './components/AppSidebar.vue';
import AppTopBar from './components/AppTopBar.vue';
import StatGrid from './components/StatGrid.vue';
import Toolbar from './components/Toolbar.vue';
import DataTable from './components/DataTable.vue';
import ProfilePanel from './components/ProfilePanel.vue';
import FormModal from './components/FormModal.vue';

const moduleName = ref('doctor');
const current = computed(() => modules[moduleName.value]);
const { request } = createApi(current);

const page = ref(getInitialPage());
const loading = ref(false);
const error = ref('');
const data = ref(null);
const filters = reactive({ search: '', status: '' });
const authVersion = ref(0);
const modal = reactive({
  visible: false,
  title: '',
  meta: '',
  description: '',
  fields: [],
  model: {},
  submit: null
});

/* ============== Auth & user info ============== */
const isLoggedIn = computed(() => {
  authVersion.value;
  return Boolean(localStorage.getItem(current.value.tokenKey));
});

const userInfo = computed(() => {
  authVersion.value;
  return JSON.parse(localStorage.getItem(current.value.userKey) || '{}');
});

/* ============== Page metadata ============== */
const pageTitle = computed(
  () => current.value.nav.find(item => item.key === page.value)?.label || current.value.title
);

const crumbs = computed(() => [current.value.title, pageTitle.value]);

const rows = computed(() => (Array.isArray(data.value) ? data.value : []));

const profileDetail = computed(() => {
  return page.value === 'profile' && data.value && !Array.isArray(data.value)
    ? data.value
    : {};
});

const profileName = computed(
  () => profileDetail.value?.user?.name || profileDetail.value?.name || userInfo.value?.name || '医师'
);

const profileRole = computed(() => {
  const profile = profileDetail.value?.profile || {};
  const title = profile.title || profileDetail.value?.title;
  const department = profile.department || profileDetail.value?.department;
  return [department, title].filter(Boolean).join(' · ') || 'Physician';
});

const profileItems = computed(() => {
  const detail = profileDetail.value;
  if (!detail || !detail.profile) return [];
  const profile = detail.profile || {};
  const user = detail.user || {};
  return [
    { label: '姓名', value: displayText(user.name || detail.name) },
    { label: '手机号', value: displayText(user.phone) },
    { label: '医生档案编号', value: displayText(detail.id || profile.id) },
    { label: '科室', value: displayText(profile.department || detail.department) },
    { label: '职称', value: displayText(profile.title || detail.title) },
    { label: '执业证号', value: displayText(profile.license_number) },
    { label: '医院/机构', value: displayText(profile.hospital || detail.hospital) },
    { label: '管理患者数', value: displayText(detail.patient_count ?? 0) },
    { label: '问诊总数', value: displayText(detail.consultation_count ?? 0) },
    {
      label: '简介 / 专长',
      value: displayText(profile.introduction || detail.introduction || detail.specialty),
      wide: true
    }
  ];
});

/* ============== Toolbar capabilities ============== */
const canSearch = computed(() => ['patients', 'users', 'products', 'doctors'].includes(page.value));
const canFilterStatus = computed(() => ['consultations', 'prescriptions', 'orders'].includes(page.value));
const createLabel = computed(() => ({ consultations: '问诊', prescriptions: '处方' }[page.value] || '记录'));
const canCreate = computed(() => ['consultations', 'prescriptions'].includes(page.value));
const showOperations = computed(() => ['patients', 'consultations', 'prescriptions'].includes(page.value));

/* ============== Stats ============== */
const stats = computed(() => {
  const value = data.value || {};
  return [
    { label: '今日问诊', value: value.today_consultations ?? 0, hint: '今日内的预约与到访总数' },
    { label: '管理患者', value: value.patient_count ?? 0, hint: '签约/绑定的慢病患者' },
    { label: '未读消息', value: value.unread_messages ?? 0, hint: '需要回复的咨询' },
    { label: '问诊总数', value: value.consultation_count ?? 0, hint: '历史累计问诊量' }
  ];
});

/* ============== Columns ============== */
const columns = computed(() => {
  const commonPeople = [
    { key: 'name', label: '姓名', value: row => row?.user?.name || row?.name || '—' },
    { key: 'phone', label: '手机号', mono: true, value: row => row?.user?.phone || row?.phone || '—' },
    { key: 'id', label: '编号', mono: true, value: row => row?.id ?? '—' }
  ];
  const maps = {
    patients: [
      ...commonPeople,
      { key: 'count', label: '监测次数', mono: true, value: row => row?.total_measurements ?? 0 },
      { key: 'latest', label: '最近监测', value: row => formatDate(row?.latest_measurement) }
    ],
    consultations: [
      { key: 'id', label: '编号', mono: true, value: row => row?.id ?? '—' },
      { key: 'status', label: '状态', badge: true, value: row => row?.status || '—' },
      { key: 'desc', label: '主诉', value: row => row?.chief_complaint || row?.symptoms || row?.description || '—' },
      { key: 'time', label: '预约时间', value: row => formatDate(row?.scheduled_time || row?.created_at) }
    ],
    prescriptions: [
      { key: 'id', label: '编号', mono: true, value: row => row?.id ?? '—' },
      { key: 'diagnosis', label: '诊断', value: row => row?.diagnosis || '—' },
      { key: 'status', label: '状态', badge: true, value: row => row?.status || '—' },
      { key: 'time', label: '创建时间', value: row => formatDate(row?.created_at) }
    ]
  };
  return maps[page.value] || [];
});

/* ============== Routing ============== */
function getInitialPage() {
  const queryPage = new URLSearchParams(location.search).get('page');
  if (queryPage) return queryPage;
  const segments = location.pathname.split('/').filter(Boolean);
  return segments[1] || 'dashboard';
}

function ensureModulePath() {
  if (!location.pathname.startsWith('/doctor')) {
    history.replaceState(null, '', `/doctor/${page.value}`);
  }
}

function setPage(target) {
  page.value = target;
  data.value = null;
  error.value = '';
  history.pushState(null, '', `/${moduleName.value}/${target}`);
  loadPage();
}

function endpointForPage() {
  return {
    dashboard: '/stats',
    patients: `/patients${buildQuery({ search: filters.search, limit: 50 })}`,
    consultations: `/consultations${buildQuery({ status: filters.status, limit: 50 })}`,
    prescriptions: `/prescriptions${buildQuery({ status: filters.status, limit: 50 })}`,
    profile: '/profile'
  }[page.value];
}

async function loadPage() {
  if (!isLoggedIn.value) return;
  const endpoint = endpointForPage();
  if (!endpoint) return;
  loading.value = true;
  error.value = '';
  try {
    data.value = await request(endpoint);
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

/* ============== Modal helpers ============== */
function openModal({ title, meta = '', description = '', fields, model, submit }) {
  modal.title = title;
  modal.meta = meta;
  modal.description = description;
  modal.fields = fields;
  modal.model = { ...model };
  modal.submit = submit;
  modal.visible = true;
}

function closeModal() {
  modal.visible = false;
  modal.title = '';
  modal.meta = '';
  modal.description = '';
  modal.fields = [];
  modal.model = {};
  modal.submit = null;
}

function updateModalField({ key, value }) {
  modal.model = { ...modal.model, [key]: value };
}

async function submitModal() {
  if (!modal.submit) return;
  const fields = modal.fields;
  const model = { ...modal.model };
  await modal.submit(normalizeFormData(fields, model));
  closeModal();
}

async function submitAction(path, options, message) {
  loading.value = true;
  error.value = '';
  try {
    await request(path, options);
    if (message) window.alert(message);
    await loadPage();
  } catch (err) {
    error.value = err.message;
    window.alert(err.message);
  } finally {
    loading.value = false;
  }
}

/* ============== Page-level CRUD ============== */
function createRecord() {
  if (page.value === 'consultations') createConsultation();
  if (page.value === 'prescriptions') createPrescription();
}

function createConsultation(row = {}) {
  openModal({
    title: row.id ? '编辑问诊' : '新增问诊',
    meta: row.id ? `#${row.id}` : 'New record',
    fields: [
      { key: 'patient_id', label: '患者档案 ID', type: 'number', emptyAsUndefined: true },
      { key: 'scheduled_time', label: '预约时间', type: 'datetime-local' },
      {
        key: 'status', label: '状态', type: 'select', options: [
          { label: '待处理', value: 'pending' },
          { label: '已确认', value: 'confirmed' },
          { label: '进行中', value: 'ongoing' },
          { label: '已完成', value: 'completed' },
          { label: '已取消', value: 'cancelled' }
        ]
      },
      { key: 'chief_complaint', label: '主诉', type: 'textarea', rows: 3, wide: true },
      { key: 'diagnosis', label: '诊断', type: 'textarea', rows: 3, wide: true },
      { key: 'treatment_plan', label: '治疗方案', type: 'textarea', rows: 3, wide: true },
      { key: 'notes', label: '备注', type: 'textarea', rows: 3, wide: true }
    ],
    model: {
      patient_id: row.patient_id ?? '',
      scheduled_time: toInputDateTime(row.scheduled_time || new Date()),
      status: row.status || 'pending',
      chief_complaint: row.chief_complaint || '',
      diagnosis: row.diagnosis || '',
      treatment_plan: row.treatment_plan || '',
      notes: row.notes || ''
    },
    submit: form => row.id
      ? submitAction(`/consultations/${row.id}`, { method: 'PUT', body: form }, '问诊已更新')
      : submitAction('/consultations', {
          method: 'POST',
          body: compactData({
            patient_id: form.patient_id,
            scheduled_time: form.scheduled_time,
            chief_complaint: form.chief_complaint
          })
        }, '问诊已创建')
  });
}

function endConsultation(row) {
  openModal({
    title: '结束问诊',
    meta: `#${row.id}`,
    fields: [
      { key: 'diagnosis', label: '诊断', type: 'textarea', rows: 4, wide: true },
      { key: 'treatment_plan', label: '治疗方案', type: 'textarea', rows: 4, wide: true },
      { key: 'prescription', label: '处方摘要', type: 'textarea', rows: 3, wide: true },
      { key: 'notes', label: '备注', type: 'textarea', rows: 3, wide: true }
    ],
    model: {
      diagnosis: row.diagnosis || '',
      treatment_plan: row.treatment_plan || '',
      prescription: '',
      notes: row.notes || ''
    },
    submit: form => submitAction(`/consultations/${row.id}/end`, { method: 'PUT', body: form }, '问诊已结束')
  });
}

function createPrescription(row = {}) {
  openModal({
    title: row.id ? '编辑处方' : '新增处方',
    meta: row.id ? `#${row.id}` : 'New prescription',
    fields: [
      { key: 'patient_id', label: '患者档案 ID', type: 'number', emptyAsUndefined: true },
      { key: 'consultation_id', label: '问诊 ID', type: 'number', emptyAsUndefined: true },
      { key: 'valid_until', label: '有效期', type: 'datetime-local', emptyAsUndefined: true },
      { key: 'product_id', label: '药品 ID', type: 'number', emptyAsUndefined: true },
      { key: 'dosage', label: '剂量' },
      { key: 'frequency', label: '频率' },
      { key: 'duration', label: '疗程' },
      { key: 'diagnosis', label: '诊断', type: 'textarea', rows: 3, wide: true },
      { key: 'notes', label: '备注', type: 'textarea', rows: 3, wide: true }
    ],
    model: {
      patient_id: row.patient_id ?? '',
      consultation_id: row.consultation_id ?? '',
      valid_until: toInputDateTime(row.valid_until),
      product_id: row.items?.[0]?.product?.id ?? '',
      dosage: row.items?.[0]?.dosage || '',
      frequency: row.items?.[0]?.frequency || '',
      duration: row.items?.[0]?.duration || '',
      diagnosis: row.diagnosis || '',
      notes: row.notes || ''
    },
    submit: form => {
      if (row.id) {
        const body = compactData({
          diagnosis: form.diagnosis,
          notes: form.notes,
          valid_until: form.valid_until
        });
        if (form.product_id) {
          body.items = [{
            product_id: form.product_id,
            dosage: form.dosage,
            frequency: form.frequency,
            duration: form.duration
          }];
        }
        return submitAction(`/prescriptions/${row.id}`, { method: 'PUT', body }, '处方已更新');
      }
      if (!form.product_id) {
        window.alert('新增处方必须填写药品 ID');
        return Promise.resolve();
      }
      return submitAction('/prescriptions', {
        method: 'POST',
        body: compactData({
          patient_id: form.patient_id,
          consultation_id: form.consultation_id,
          diagnosis: form.diagnosis,
          notes: form.notes,
          valid_until: form.valid_until,
          items: [{
            product_id: form.product_id,
            dosage: form.dosage,
            frequency: form.frequency,
            duration: form.duration
          }]
        })
      }, '处方已创建');
    }
  });
}

function sendPatientMessage(row = {}) {
  openModal({
    title: '发送消息',
    meta: row.user?.name ? `致 ${row.user.name}` : '致 患者',
    fields: [
      { key: 'patient_id', label: '患者档案 ID', type: 'number', emptyAsUndefined: true },
      { key: 'content', label: '消息内容', type: 'textarea', rows: 5, wide: true }
    ],
    model: { patient_id: row.id ?? '', content: '' },
    submit: form => submitAction('/messages', {
      method: 'POST',
      body: { patient_id: form.patient_id, content: form.content }
    }, '消息已发送')
  });
}

function createFollowUp(row = {}) {
  openModal({
    title: '新建随访',
    meta: row.user?.name || '患者',
    fields: [
      { key: 'patient_id', label: '患者档案 ID', type: 'number', emptyAsUndefined: true },
      { key: 'scheduled_date', label: '随访时间', type: 'datetime-local' },
      {
        key: 'follow_up_type', label: '随访方式', type: 'select', options: [
          { label: '电话', value: 'phone' },
          { label: '视频', value: 'video' },
          { label: '线下', value: 'in_person' }
        ]
      },
      { key: 'notes', label: '随访计划', type: 'textarea', rows: 4, wide: true }
    ],
    model: {
      patient_id: row.id ?? '',
      scheduled_date: toInputDateTime(new Date()),
      follow_up_type: 'phone',
      notes: ''
    },
    submit: form => submitAction('/follow-ups', { method: 'POST', body: form }, '随访已创建')
  });
}

function editProfile() {
  const detail = profileDetail.value || {};
  const profile = detail.profile || {};
  openModal({
    title: '编辑个人资料',
    meta: 'Profile',
    fields: [
      { key: 'department', label: '科室' },
      { key: 'title', label: '职称' },
      { key: 'license_number', label: '执业证号' },
      { key: 'hospital', label: '医院 / 机构' },
      { key: 'introduction', label: '简介 / 专长', type: 'textarea', rows: 5, wide: true }
    ],
    model: {
      department: profile.department || detail.department || '',
      title: profile.title || detail.title || '',
      license_number: profile.license_number || '',
      hospital: profile.hospital || detail.hospital || '',
      introduction: profile.introduction || detail.introduction || detail.specialty || ''
    },
    submit: form => submitAction('/profile', { method: 'PUT', body: form }, '个人资料已更新')
  });
}

function rowActions(row) {
  if (page.value === 'patients') {
    return [
      { label: '发消息', handler: () => sendPatientMessage(row) },
      { label: '健康数据', handler: () => viewPatientMeasurements(row) },
      { label: '建随访', handler: () => createFollowUp(row) },
      { label: '开处方', handler: () => createPrescription({ patient_id: row.id }) },
      {
        label: '解除签约',
        danger: true,
        handler: () => submitAction(`/patients/${row.id}/sign`, { method: 'DELETE' }, '已解除签约')
      }
    ];
  }
  if (page.value === 'consultations') {
    return [
      { label: '编辑', handler: () => createConsultation(row) },
      ...(row.status !== 'completed' && row.status !== 'cancelled'
        ? [{ label: '加入视频', handler: () => joinVideoCall(row) }]
        : []),
      ...(row.status === 'ongoing'
        ? [{ label: '结束视频', danger: true, handler: () => endVideoCall(row) }]
        : []),
      ...(row.status !== 'ongoing' && row.status !== 'completed'
        ? [{ label: '开始', handler: () => submitAction(`/consultations/${row.id}/start`, { method: 'PUT' }, '问诊已开始') }]
        : []),
      ...(row.status !== 'completed'
        ? [{ label: '结束', handler: () => endConsultation(row) }]
        : [])
    ];
  }
  if (page.value === 'prescriptions') {
    return [{ label: '编辑', handler: () => createPrescription(row) }];
  }
  return [];
}

async function joinVideoCall(row) {
  loading.value = true;
  error.value = '';
  try {
    const room = await request(`/video-calls/${row.id}/join`, { method: 'POST' });
    const lines = [
      `问诊编号：${room.consultation_id}`,
      `房间号：${room.room_id}`,
      `患者：${room.patient_name || room.patient_id || '—'}`,
      `状态：${room.status}`,
      `本端推流：${room.local_push_url || '未配置 VIDEO_PUSH_BASE_URL'}`,
      `患者画面：${room.remote_play_url || '未配置 VIDEO_PLAY_BASE_URL'}`
    ];
    openModal({
      title: '视频问诊房间',
      meta: room.room_id,
      description: room.stream_ready
        ? '房间已建立，可使用下方音视频地址接入。'
        : '业务房间已建立；请配置后端 VIDEO_PUSH_BASE_URL / VIDEO_PLAY_BASE_URL 后启用真实音视频流。',
      fields: [
        { key: 'room', label: '房间信息', type: 'textarea', rows: 8, wide: true }
      ],
      model: {
        room: lines.join('\n')
      },
      submit: null
    });
    await loadPage();
  } catch (err) {
    error.value = err.message;
    window.alert(err.message || '加入视频问诊失败');
  } finally {
    loading.value = false;
  }
}

async function endVideoCall(row) {
  if (!window.confirm('确定要结束该视频问诊吗？')) return;
  await submitAction(`/video-calls/${row.id}/end`, {
    method: 'PUT',
    body: { notes: '医生端结束视频问诊' }
  }, '视频问诊已结束');
}

async function viewPatientMeasurements(row) {
  loading.value = true;
  error.value = '';
  try {
    const records = await request(`/patients/${row.id}/measurements${buildQuery({ days: 365, limit: 50 })}`);
    const lines = (records || []).map(item => {
      const value = item.value2 === null || item.value2 === undefined
        ? `${item.value1}`
        : `${item.value1}/${item.value2}`;
      return `${formatDate(item.measured_at)}  ${item.type}  ${value}  ${item.risk_level || 'normal'}${item.notes ? `  ${item.notes}` : ''}`;
    });
    openModal({
      title: '患者健康数据',
      meta: `#${row.id}`,
      description: lines.length ? `最近 ${lines.length} 条真实监测记录` : '该患者暂无监测数据',
      fields: [
        { key: 'measurements', label: '监测记录', type: 'textarea', rows: 12, wide: true }
      ],
      model: {
        measurements: lines.join('\n') || '暂无数据'
      },
      submit: null
    });
  } catch (err) {
    error.value = err.message;
    window.alert(err.message || '健康数据加载失败');
  } finally {
    loading.value = false;
  }
}

/* ============== Auth actions ============== */
async function login(form) {
  loading.value = true;
  error.value = '';
  try {
    const result = await request('/login', {
      method: 'POST',
      body: { phone: form.phone, password: form.password }
    });
    localStorage.setItem(current.value.tokenKey, result.token);
    localStorage.setItem(current.value.userKey, JSON.stringify(result));
    authVersion.value += 1;
    setPage('dashboard');
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

function logout() {
  localStorage.removeItem(current.value.tokenKey);
  localStorage.removeItem(current.value.userKey);
  authVersion.value += 1;
  data.value = null;
}

function redirectToModule(target) {
  if (target === moduleName.value) return;
  const host = target === 'admin' ? 'admin.yun-an.xyz' : 'doctor.yun-an.xyz';
  window.location.href = `${window.location.protocol}//${host}/${target}/dashboard`;
}

/* ============== Lifecycle ============== */
window.addEventListener('popstate', () => {
  page.value = getInitialPage();
  ensureModulePath();
  loadPage();
});

onMounted(() => {
  ensureModulePath();
  loadPage();
});
</script>
