<template>
  <aside class="sidebar">
    <div class="brand">
      <h1>{{ current.title }}</h1>
      <p>{{ subtitle }}</p>
    </div>

    <button
      v-for="item in current.nav"
      :key="item.key"
      class="nav-item"
      :class="{ active: page === item.key }"
      @click="$emit('navigate', item.key)"
    >
      {{ item.label }}
    </button>

    <div class="sidebar__footer">
      <span>{{ apiLabel }}</span>
      <span>{{ buildLabel }}</span>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  current: { type: Object, required: true },
  userInfo: { type: Object, default: () => ({}) },
  page: { type: String, required: true },
  buildLabel: { type: String, default: 'v1.0 · 2026 春' }
});

defineEmits(['navigate']);

const subtitle = computed(() => {
  const name = props.userInfo?.name;
  return name ? `${name} · ${props.current.roleName}` : props.current.roleName;
});

const apiLabel = computed(() => {
  try {
    const url = new URL(props.current.apiHost);
    return `${url.host}${props.current.prefix}`;
  } catch {
    return `${props.current.apiHost}${props.current.prefix}`;
  }
});
</script>
