<template>
  <div class="toolbar reveal" data-delay="2">
    <div class="filters">
      <input
        v-if="canSearch"
        :value="search"
        :placeholder="searchPlaceholder"
        @input="$emit('update:search', $event.target.value.trim())"
        @keyup.enter="$emit('query')"
      />
      <select
        v-if="canFilterStatus"
        :value="status"
        @change="$emit('update:status', $event.target.value)"
      >
        <option value="">全部状态</option>
        <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <button v-if="canSearch || canFilterStatus" class="secondary-btn" @click="$emit('query')">查 询</button>
    </div>
    <div class="actions">
      <slot />
      <button v-if="canCreate" class="primary-btn" @click="$emit('create')">
        + 新增{{ createLabel }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  canSearch: { type: Boolean, default: false },
  canFilterStatus: { type: Boolean, default: false },
  canCreate: { type: Boolean, default: false },
  search: { type: String, default: '' },
  status: { type: String, default: '' },
  searchPlaceholder: { type: String, default: '输入关键词搜索' },
  createLabel: { type: String, default: '记录' },
  statusOptions: {
    type: Array,
    default: () => [
      { label: '待处理', value: 'pending' },
      { label: '已通过', value: 'approved' },
      { label: '已驳回', value: 'rejected' },
      { label: '已发货', value: 'shipped' },
      { label: '已完成', value: 'completed' }
    ]
  }
});

defineEmits(['update:search', 'update:status', 'query', 'create']);
</script>
