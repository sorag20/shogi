<template>
  <div v-if="error" class="error-message">
    <div class="error-content">
      <span class="error-icon">⚠️</span>
      <div class="error-text">
        <p class="error-title">{{ title }}</p>
        <p class="error-detail">{{ error }}</p>
      </div>
      <button v-if="dismissible" class="close-btn" @click="$emit('dismiss')">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  error: string | null
  title?: string
  dismissible?: boolean
}

withDefaults(defineProps<Props>(), {
  title: 'Error',
  dismissible: true,
})

defineEmits<{
  dismiss: []
}>()
</script>

<style scoped>
.error-message {
  margin: 10px 0;
}

.error-content {
  display: flex;
  align-items: center;
  background-color: #fee;
  border: 1px solid #fcc;
  border-radius: 4px;
  padding: 12px;
  gap: 10px;
}

.error-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.error-text {
  flex: 1;
}

.error-title {
  margin: 0;
  font-weight: bold;
  color: #c33;
  font-size: 14px;
}

.error-detail {
  margin: 4px 0 0 0;
  color: #666;
  font-size: 13px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
  padding: 0;
  flex-shrink: 0;
}

.close-btn:hover {
  color: #333;
}
</style>
