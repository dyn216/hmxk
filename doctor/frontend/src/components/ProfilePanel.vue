<template>
  <section class="card profile-card reveal" data-delay="3">
    <header class="profile-card__hero">
      <div class="profile-card__avatar">{{ initial }}</div>
      <div>
        <p class="eyebrow">Doctor profile</p>
        <h3 class="profile-card__name">{{ name }}</h3>
        <p class="profile-card__role">{{ role }}</p>
      </div>
    </header>

    <div v-if="items.length" class="profile-grid">
      <div
        v-for="item in items"
        :key="item.label"
        class="profile-item"
        :class="{ wide: item.wide }"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
    </div>
    <div v-else class="empty">
      <span class="empty__icon">~</span>
      <p>暂无个人资料，可点击右上角“编辑”补充。</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  items: { type: Array, default: () => [] },
  name: { type: String, default: '医师' },
  role: { type: String, default: 'Physician' }
});

const initial = computed(() => {
  const text = (props.name || '医').trim();
  return text.slice(0, 1).toUpperCase();
});
</script>
