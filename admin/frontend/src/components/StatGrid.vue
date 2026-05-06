<template>
  <section class="stats-grid">
    <article
      v-for="(item, index) in items"
      :key="item.label"
      class="stat-card reveal"
      :data-delay="(index % 4) + 1"
    >
      <div class="stat-card__label" :data-index="formatIndex(index + 1)">
        {{ item.label }}
      </div>
      <strong>{{ formatValue(item.value) }}</strong>
      <small v-if="item.hint">{{ item.hint }}</small>
    </article>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  items: { type: Array, required: true }
});

function formatIndex(n) {
  return String(n).padStart(2, '0');
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'number') return value.toLocaleString('zh-CN');
  return value;
}
</script>
