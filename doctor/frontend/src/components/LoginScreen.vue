<template>
  <section class="login-page">
    <div class="login-hero">
      <div class="login-hero__mark">{{ brand }}</div>
      <div>
        <p class="eyebrow">Chronic Care Console</p>
        <h1>从 <em>诊室</em> 到 <em>居家</em>，<br />一段连续的关照。</h1>
      </div>
      <p>
        慢性病管理平台为医生、患者与运营提供一处协同的工作面：处方流转、随访留档、设备监测、订单履约都在一个秩序井然的台面上完成。
      </p>
      <dl class="login-hero__meta">
        <div>
          <dt>当前接入</dt>
          <dd>{{ current.roleName }}</dd>
        </div>
        <div>
          <dt>API 端点</dt>
          <dd class="mono">{{ shortHost }}</dd>
        </div>
        <div>
          <dt>版本</dt>
          <dd class="mono">v1.0 · 2026</dd>
        </div>
      </dl>
    </div>

    <form class="login-card" @submit.prevent="$emit('submit', form)">
      <div class="link-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          :class="{ active: tab.key === module }"
          @click="$emit('switch-module', tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>
      <h2>
        {{ current.roleName }}登录
        <small>Sign in</small>
      </h2>
      <p class="sub-title">{{ current.apiHost }}{{ current.prefix }}</p>

      <div v-if="error" class="error">{{ error }}</div>

      <div class="form-field">
        <label>手机号</label>
        <input
          v-model.trim="form.phone"
          autocomplete="username"
          placeholder="13900000000"
          required
        />
      </div>
      <div class="form-field">
        <label>密码</label>
        <input
          v-model="form.password"
          type="password"
          autocomplete="current-password"
          placeholder="••••••••"
          required
        />
      </div>

      <button class="primary-btn full" type="submit" :disabled="loading">
        {{ loading ? '登录中…' : '登 录' }}
      </button>
    </form>
  </section>
</template>

<script setup>
import { computed, reactive } from 'vue';

const props = defineProps({
  module: { type: String, required: true },
  current: { type: Object, required: true },
  error: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  brand: { type: String, default: '诊室手记 · Clinical Notebook' },
  tabs: {
    type: Array,
    default: () => [
      { key: 'doctor', label: '医生端' },
      { key: 'admin', label: '管理端' }
    ]
  }
});

defineEmits(['submit', 'switch-module']);

const form = reactive({ phone: '', password: '' });

const shortHost = computed(() => {
  try {
    const url = new URL(props.current.apiHost);
    return url.host;
  } catch {
    return props.current.apiHost;
  }
});
</script>
