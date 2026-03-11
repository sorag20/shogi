<template>
  <div v-if="isLoading" class="loading-spinner">
    <div class="spinner"></div>
    <p>{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  isLoading: boolean
  message?: string
}

withDefaults(defineProps<Props>(), {
  message: 'Loading...',
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

p {
  color: #666;
  font-size: 14px;
}
</style>
