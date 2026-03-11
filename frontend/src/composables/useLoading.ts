import { ref, computed } from 'vue'

export function useLoading() {
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const setLoading = (loading: boolean) => {
    isLoading.value = loading
  }

  const setError = (err: string | null) => {
    error.value = err
  }

  const clearError = () => {
    error.value = null
  }

  const hasError = computed(() => error.value !== null)

  return {
    isLoading,
    error,
    hasError,
    setLoading,
    setError,
    clearError,
  }
}
