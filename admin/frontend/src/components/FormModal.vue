<template>
  <transition name="modal">
    <div v-if="visible" class="modal-mask" @click.self="$emit('close')">
      <form class="modal-card" @submit.prevent="$emit('submit')">
        <header class="modal-head">
          <h3>
            {{ title }}
            <small v-if="meta">{{ meta }}</small>
          </h3>
          <button type="button" class="ghost-btn compact" @click="$emit('close')">
            关 闭
          </button>
        </header>

        <p v-if="description" class="modal-description">{{ description }}</p>

        <div class="modal-grid">
          <label
            v-for="field in fields"
            :key="field.key"
            class="modal-field"
            :class="{ wide: field.wide }"
          >
            <span>{{ field.label }}</span>

            <textarea
              v-if="field.type === 'textarea'"
              :value="model[field.key]"
              :rows="field.rows || 4"
              :placeholder="field.placeholder || ''"
              @input="updateField(field.key, $event.target.value)"
            />

            <select
              v-else-if="field.type === 'select'"
              :value="model[field.key]"
              @change="updateField(field.key, $event.target.value)"
            >
              <option
                v-for="option in field.options"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>

            <span
              v-else-if="field.type === 'checkbox'"
              class="check-field"
            >
              <input
                type="checkbox"
                :checked="!!model[field.key]"
                @change="updateField(field.key, $event.target.checked)"
              />
              {{ field.checkLabel || '是' }}
            </span>

            <input
              v-else
              :type="field.type || 'text'"
              :value="model[field.key]"
              :placeholder="field.placeholder || ''"
              @input="updateField(field.key, $event.target.value)"
            />
          </label>
        </div>

        <footer class="modal-actions">
          <button type="button" class="secondary-btn" @click="$emit('close')">取 消</button>
          <button class="primary-btn" type="submit">保 存</button>
        </footer>
      </form>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
  meta: { type: String, default: '' },
  description: { type: String, default: '' },
  fields: { type: Array, default: () => [] },
  model: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['submit', 'close', 'update:field']);

function updateField(key, value) {
  emit('update:field', { key, value });
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.18s ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
</style>
