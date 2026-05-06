<template>
  <section class="card table-card reveal" data-delay="3">
    <div class="table-card__scroll">
      <table v-if="rows.length">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
            <th v-if="showOperations">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in rows" :key="row.id || index">
            <td
              v-for="column in columns"
              :key="column.key"
              :class="{ mono: column.mono }"
            >
              <span
                v-if="column.badge"
                class="badge"
                :class="badgeClass(column.value(row), column.badgeMap)"
              >
                {{ column.value(row) }}
              </span>
              <span v-else>{{ column.value(row) }}</span>
            </td>
            <td v-if="showOperations">
              <div class="row-actions">
                <button
                  v-for="action in resolveActions(row)"
                  :key="action.label"
                  :class="action.danger ? 'danger-btn compact' : 'secondary-btn compact'"
                  @click="action.handler"
                >
                  {{ action.label }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">
        <span class="empty__icon">∅</span>
        <p>暂未检索到记录，调整筛选条件再试。</p>
      </div>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  rows: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] },
  showOperations: { type: Boolean, default: false },
  rowActions: { type: Function, default: null }
});

function resolveActions(row) {
  return props.rowActions ? props.rowActions(row) : [];
}

function badgeClass(value, map) {
  if (!value) return 'is-muted';
  const v = String(value).toLowerCase();
  if (map && map[v]) return map[v];
  if (['pending', 'paid', 'ongoing'].includes(v)) return 'is-warning';
  if (['approved', 'completed', 'shipped', 'confirmed'].includes(v)) return 'is-success';
  if (['rejected', 'cancelled'].includes(v)) return 'is-danger';
  return '';
}
</script>
