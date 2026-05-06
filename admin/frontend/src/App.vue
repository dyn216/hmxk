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
        <button class="ghost-btn" @click="redirectToModule('doctor')">前往医生端</button>
        <button class="danger-btn" @click="logout">退出登录</button>
      </AppTopBar>

      <div v-if="loading" class="card loading">载入数据中</div>
      <div v-else-if="error" class="card error">{{ error }}</div>

      <template v-else>
        <template v-if="page === 'dashboard'">
          <StatGrid :items="stats" />
          <section class="card quick-actions reveal" data-delay="3">
            <h3>运营动作</h3>
            <p>常用的用户、药品、订单与处方审核入口都收纳在此处。</p>
            <div class="row-actions">
              <button class="primary-btn" @click="setPage('users')">管理用户</button>
              <button class="primary-btn" @click="setPage('products')">维护药品</button>
              <button class="secondary-btn" @click="setPage('orders')">订单履约</button>
              <button class="secondary-btn" @click="setPage('prescriptions')">处方审核</button>
              <button class="secondary-btn" @click="setPage('doctors')">医生档案</button>
            </div>
          </section>
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
          />
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
import FormModal from './components/FormModal.vue';

const moduleName = ref('admin');
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

/* ============== Auth ============== */
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

const canSearch = computed(() => ['patients', 'users', 'products', 'doctors'].includes(page.value));
const canFilterStatus = computed(() => ['consultations', 'prescriptions', 'orders'].includes(page.value));
const createLabel = computed(() => ({ users: '用户', products: '药品' }[page.value] || '记录'));
const canCreate = computed(() => ['users', 'products'].includes(page.value));
const showOperations = computed(
  () => ['users', 'products', 'orders', 'prescriptions', 'doctors', 'patients'].includes(page.value)
);

/* ============== Stats ============== */
const stats = computed(() => {
  const value = data.value || {};
  return [
    { label: '总用户', value: value.total_users ?? 0, hint: '平台累计注册用户' },
    { label: '患者数', value: value.total_patients ?? 0, hint: '已建立健康档案的患者' },
    { label: '医生数', value: value.total_doctors ?? 0, hint: '在岗签约医生' },
    { label: '在线设备', value: value.online_devices ?? 0, hint: '近 24h 上传过数据' }
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
    users: [
      { key: 'name', label: '姓名', value: row => row?.name || '—' },
      { key: 'phone', label: '手机号', mono: true, value: row => row?.phone || '—' },
      { key: 'role', label: '角色', badge: true, value: row => row?.role || '—' },
      { key: 'status', label: '状态', badge: true, value: row => (row?.status ? 'approved' : 'rejected') }
    ],
    products: [
      { key: 'name', label: '名称', value: row => row?.name || '—' },
      { key: 'specification', label: '规格', value: row => row?.specification || '—' },
      { key: 'category', label: '分类', value: row => row?.category || '—' },
      { key: 'manufacturer', label: '厂家', value: row => row?.manufacturer || '—' },
      { key: 'price', label: '价格', mono: true, value: row => `¥${row?.price ?? 0}/${row?.unit || '件'}` },
      { key: 'stock', label: '库存', mono: true, value: row => row?.stock ?? 0 },
      { key: 'is_prescription', label: '处方药', value: row => (row?.is_prescription ? '是' : '否') },
      { key: 'status', label: '状态', badge: true, value: row => (row?.status ? 'approved' : 'rejected') }
    ],
    orders: [
      { key: 'order', label: '订单号', mono: true, value: row => row?.order_no || row?.id || '—' },
      { key: 'amount', label: '金额', mono: true, value: row => `¥${row?.total_amount ?? 0}` },
      { key: 'status', label: '状态', badge: true, value: row => row?.status || '—' },
      { key: 'time', label: '创建时间', value: row => formatDate(row?.created_at) }
    ],
    prescriptions: [
      { key: 'id', label: '编号', mono: true, value: row => row?.id ?? '—' },
      { key: 'diagnosis', label: '诊断', value: row => row?.diagnosis || '—' },
      { key: 'status', label: '状态', badge: true, value: row => row?.status || '—' },
      { key: 'time', label: '创建时间', value: row => formatDate(row?.created_at) }
    ],
    doctors: commonPeople,
    patients: commonPeople
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
  if (!location.pathname.startsWith('/admin')) {
    history.replaceState(null, '', `/admin/${page.value}`);
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
    users: `/users${buildQuery({ search: filters.search, limit: 50 })}`,
    products: `/products${buildQuery({ search: filters.search, limit: 50 })}`,
    orders: `/orders${buildQuery({ status: filters.status, limit: 50 })}`,
    prescriptions: `/prescriptions${buildQuery({ status: filters.status, limit: 50 })}`,
    doctors: `/doctors${buildQuery({ search: filters.search, limit: 50 })}`,
    patients: `/patients${buildQuery({ search: filters.search, limit: 50 })}`
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
  await modal.submit(normalizeFormData(modal.fields, { ...modal.model }));
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

function promptValue(label, value = '') {
  const result = window.prompt(label, value ?? '');
  return result === null ? null : result.trim();
}

/* ============== Page actions ============== */
function createRecord() {
  if (page.value === 'users') createUser();
  if (page.value === 'products') createProduct();
}

function createUser() {
  openModal({
    title: '新增用户',
    meta: 'New user',
    fields: [
      { key: 'name', label: '姓名' },
      { key: 'phone', label: '手机号' },
      {
        key: 'role', label: '角色', type: 'select', options: [
          { label: '患者', value: 'patient' },
          { label: '医生', value: 'doctor' },
          { label: '管理员', value: 'admin' }
        ]
      },
      { key: 'password', label: '初始密码', placeholder: '默认 123456' }
    ],
    model: { name: '', phone: '', role: 'patient', password: '123456' },
    submit: form => {
      if (!form.phone || !form.name) {
        window.alert('请填写姓名和手机号');
        return Promise.resolve();
      }
      return submitAction('/users', {
        method: 'POST',
        body: { phone: form.phone, name: form.name, role: form.role, password: form.password || '123456' }
      }, '用户已创建');
    }
  });
}

function editUser(row) {
  openModal({
    title: '编辑用户',
    meta: `#${row.id}`,
    fields: [
      { key: 'name', label: '姓名' },
      { key: 'phone', label: '手机号' },
      { key: 'password', label: '新密码（留空不修改）', emptyAsUndefined: true }
    ],
    model: { name: row.name || '', phone: row.phone || '', password: '' },
    submit: form => submitAction(`/users/${row.id}`, {
      method: 'PUT',
      body: compactData({ name: form.name, phone: form.phone, password: form.password || undefined })
    }, '用户已更新')
  });
}

function toggleUserStatus(row) {
  const next = !row.status;
  if (!window.confirm(`确定${next ? '启用' : '禁用'}该用户？`)) return;
  submitAction(`/users/${row.id}/status`, {
    method: 'PUT',
    body: { status: next }
  }, `用户已${next ? '启用' : '禁用'}`);
}

function productFields() {
  return [
    { key: 'name', label: '药品名称', wide: true },
    { key: 'specification', label: '规格' },
    { key: 'category', label: '分类' },
    { key: 'manufacturer', label: '生产厂家' },
    { key: 'approval_number', label: '批准文号' },
    { key: 'price', label: '价格', type: 'number' },
    { key: 'stock', label: '库存', type: 'number' },
    { key: 'unit', label: '单位' },
    { key: 'image_url', label: '图片地址', type: 'url', wide: true },
    { key: 'description', label: '药品说明', type: 'textarea', rows: 4, wide: true },
    { key: 'usage', label: '用法用量', type: 'textarea', rows: 4, wide: true },
    { key: 'precautions', label: '注意事项', type: 'textarea', rows: 4, wide: true },
    { key: 'is_prescription', label: '处方药', type: 'checkbox', checkLabel: '需要处方' },
    { key: 'status', label: '上架状态', type: 'checkbox', checkLabel: '上架销售' }
  ];
}

function productModel(row = {}) {
  return {
    name: row.name || '',
    specification: row.specification || '',
    category: row.category || 'medicine',
    manufacturer: row.manufacturer || '',
    approval_number: row.approval_number || '',
    price: row.price ?? 0,
    stock: row.stock ?? 0,
    unit: row.unit || '盒',
    image_url: row.image_url || '',
    description: row.description || '',
    usage: row.usage || '',
    precautions: row.precautions || '',
    is_prescription: Boolean(row.is_prescription),
    status: row.status ?? true
  };
}

function createProduct() {
  openModal({
    title: '新增药品',
    meta: 'New product',
    description: '填写药品基础信息、库存价格、处方属性和说明信息。',
    fields: productFields(),
    model: productModel(),
    submit: form => {
      if (!form.name) {
        window.alert('请填写药品名称');
        return Promise.resolve();
      }
      if (form.price === undefined) {
        window.alert('请填写价格');
        return Promise.resolve();
      }
      return submitAction('/products', { method: 'POST', body: form }, '药品已创建');
    }
  });
}

function editProduct(row) {
  openModal({
    title: '编辑药品',
    meta: `#${row.id}`,
    description: '可维护药品规格、厂家、批准文号、库存、价格、说明、用法和注意事项。',
    fields: productFields(),
    model: productModel(row),
    submit: form => {
      if (!form.name) {
        window.alert('请填写药品名称');
        return Promise.resolve();
      }
      return submitAction(`/products/${row.id}`, { method: 'PUT', body: form }, '药品已更新');
    }
  });
}

function toggleProductStatus(row) {
  const next = !row.status;
  if (!window.confirm(`确定${next ? '上架' : '下架'}该商品？`)) return;
  submitAction(`/products/${row.id}`, {
    method: 'PUT',
    body: { status: next }
  }, `商品已${next ? '上架' : '下架'}`);
}

function deleteRecord(path, confirmText, message) {
  if (!window.confirm(confirmText)) return;
  submitAction(path, { method: 'DELETE' }, message);
}

function shipOrder(row) {
  const trackingNumber = promptValue('物流单号（可留空）', '');
  if (trackingNumber === null) return;
  const note = promptValue('发货备注（可留空）', '');
  if (note === null) return;
  submitAction(`/orders/${row.id}/ship`, {
    method: 'PUT',
    body: compactData({
      tracking_number: trackingNumber || undefined,
      note: note || undefined
    })
  }, '订单已发货');
}

function cancelOrder(row) {
  if (!window.confirm('确定取消该订单？')) return;
  submitAction(`/orders/${row.id}/cancel`, { method: 'PUT' }, '订单已取消');
}

function updatePrescriptionStatus(row, status) {
  const label = status === 'approved' ? '通过' : '驳回';
  if (!window.confirm(`确定${label}该处方？`)) return;
  const notes = status === 'rejected'
    ? promptValue('驳回原因（可留空）', row.notes || '')
    : row.notes;
  if (notes === null) return;
  submitAction(`/prescriptions/${row.id}`, {
    method: 'PUT',
    body: compactData({ status, notes: notes || undefined })
  }, `处方已${label}`);
}

function editPrescription(row) {
  openModal({
    title: '处方审核',
    meta: `#${row.id}`,
    description: `患者档案 ID：${row.patient_id ?? '—'}　医生：${row.doctor?.name || '—'}`,
    fields: [
      {
        key: 'status', label: '审核状态', type: 'select', options: [
          { label: '待审核', value: 'pending' },
          { label: '已通过', value: 'approved' },
          { label: '已驳回', value: 'rejected' }
        ]
      },
      { key: 'valid_until', label: '有效期', type: 'datetime-local', emptyAsUndefined: true },
      { key: 'product_id', label: '药品 ID', type: 'number', emptyAsUndefined: true },
      { key: 'dosage', label: '剂量' },
      { key: 'frequency', label: '频率' },
      { key: 'duration', label: '疗程' },
      { key: 'diagnosis', label: '诊断', type: 'textarea', rows: 3, wide: true },
      { key: 'notes', label: '审核备注', type: 'textarea', rows: 4, wide: true }
    ],
    model: {
      status: row.status || 'pending',
      valid_until: toInputDateTime(row.valid_until),
      product_id: row.items?.[0]?.product?.id ?? '',
      dosage: row.items?.[0]?.dosage || '',
      frequency: row.items?.[0]?.frequency || '',
      duration: row.items?.[0]?.duration || '',
      diagnosis: row.diagnosis || '',
      notes: row.notes || ''
    },
    submit: form => {
      const body = compactData({
        status: form.status,
        valid_until: form.valid_until,
        diagnosis: form.diagnosis,
        notes: form.notes
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
  });
}

function editDoctor(row) {
  const profile = row.profile || {};
  openModal({
    title: '医生档案',
    meta: `#${row.id}`,
    fields: [
      { key: 'name', label: '姓名' },
      { key: 'phone', label: '手机号' },
      { key: 'department', label: '科室' },
      { key: 'title', label: '职称' },
      { key: 'license_number', label: '执业证号' },
      { key: 'hospital', label: '医院 / 机构' },
      { key: 'user_status', label: '账号状态', type: 'checkbox', checkLabel: '启用账号' },
      { key: 'introduction', label: '简介 / 专长', type: 'textarea', rows: 5, wide: true }
    ],
    model: {
      name: row.name || row.user?.name || '',
      phone: row.user?.phone || '',
      department: row.department || profile.department || '',
      title: row.title || profile.title || '',
      license_number: profile.license_number || '',
      hospital: row.hospital || profile.hospital || '',
      user_status: row.user?.status !== false,
      introduction: row.introduction || profile.introduction || ''
    },
    submit: form => submitAction(`/doctors/${row.id}`, { method: 'PUT', body: form }, '医生档案已更新')
  });
}

function editPatient(row) {
  const profile = row.profile || {};
  openModal({
    title: '患者档案',
    meta: `#${row.id}`,
    description: `监测次数：${row.total_measurements ?? 0}　最近监测：${formatDate(row.latest_measurement)}`,
    fields: [
      { key: 'name', label: '姓名' },
      { key: 'phone', label: '手机号' },
      { key: 'age', label: '年龄', type: 'number', emptyAsUndefined: true },
      {
        key: 'gender', label: '性别', type: 'select', options: [
          { label: '未填写', value: '' },
          { label: '男', value: '男' },
          { label: '女', value: '女' }
        ], emptyAsUndefined: true
      },
      { key: 'height', label: '身高 (cm)', type: 'number', emptyAsUndefined: true },
      { key: 'weight', label: '体重 (kg)', type: 'number', emptyAsUndefined: true },
      { key: 'doctor_id', label: '绑定医生 ID', type: 'number', emptyAsUndefined: true },
      { key: 'emergency_contact', label: '紧急联系人' },
      { key: 'emergency_phone', label: '紧急联系电话' },
      { key: 'address', label: '地址', type: 'textarea', rows: 2, wide: true },
      { key: 'chronic_diseases', label: '慢性病史', type: 'textarea', rows: 3, wide: true },
      { key: 'allergies', label: '过敏史', type: 'textarea', rows: 3, wide: true }
    ],
    model: {
      name: row.user?.name || row.name || '',
      phone: row.user?.phone || '',
      age: profile.age ?? '',
      gender: profile.gender || '',
      height: profile.height ?? '',
      weight: profile.weight ?? '',
      doctor_id: profile.doctor_id ?? '',
      emergency_contact: profile.emergency_contact || '',
      emergency_phone: profile.emergency_phone || '',
      address: profile.address || '',
      chronic_diseases: profile.chronic_diseases || '',
      allergies: profile.allergies || ''
    },
    submit: form => submitAction(`/patients/${row.id}`, { method: 'PUT', body: form }, '患者档案已更新')
  });
}

function rowActions(row) {
  if (page.value === 'users') {
    return [
      { label: '编辑', handler: () => editUser(row) },
      { label: row.status ? '禁用' : '启用', handler: () => toggleUserStatus(row) },
      {
        label: '删除',
        danger: true,
        handler: () => deleteRecord(`/users/${row.id}`, '确定删除该用户？', '用户已删除')
      }
    ];
  }
  if (page.value === 'products') {
    return [
      { label: '编辑', handler: () => editProduct(row) },
      { label: row.status ? '下架' : '上架', handler: () => toggleProductStatus(row) },
      {
        label: '删除',
        danger: true,
        handler: () => deleteRecord(`/products/${row.id}`, '确定删除该商品？', '商品已删除或下架')
      }
    ];
  }
  if (page.value === 'orders') {
    return [
      ...(row.status === 'paid' ? [{ label: '发货', handler: () => shipOrder(row) }] : []),
      ...(!['completed', 'cancelled'].includes(row.status)
        ? [{ label: '取消', danger: true, handler: () => cancelOrder(row) }]
        : [])
    ];
  }
  if (page.value === 'prescriptions') {
    return [
      { label: '编辑', handler: () => editPrescription(row) },
      ...(row.status !== 'approved'
        ? [{ label: '通过', handler: () => updatePrescriptionStatus(row, 'approved') }]
        : []),
      ...(row.status !== 'rejected'
        ? [{ label: '驳回', danger: true, handler: () => updatePrescriptionStatus(row, 'rejected') }]
        : [])
    ];
  }
  if (page.value === 'doctors') return [{ label: '编辑', handler: () => editDoctor(row) }];
  if (page.value === 'patients') return [{ label: '编辑', handler: () => editPatient(row) }];
  return [];
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
