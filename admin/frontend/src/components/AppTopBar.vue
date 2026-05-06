<template>
  <header class="topbar reveal" data-delay="1">
    <div class="topbar__heading">
      <div class="topbar__crumbs">
        <span v-for="(item, index) in crumbs" :key="index">{{ item }}</span>
      </div>
      <h2>{{ title }}</h2>
    </div>
    <div class="actions">
      <slot />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  crumbs: { type: Array, default: () => [] }
});
</script>
