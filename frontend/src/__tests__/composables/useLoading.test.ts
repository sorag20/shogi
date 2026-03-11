import { describe, it, expect } from 'vitest'
import { useLoading } from '../../composables/useLoading'

describe('useLoading', () => {
  it('should initialize with default values', () => {
    const { isLoading, error, hasError } = useLoading()
    expect(isLoading.value).toBe(false)
    expect(error.value).toBeNull()
    expect(hasError.value).toBe(false)
  })

  it('should set loading state', () => {
    const { isLoading, setLoading } = useLoading()
    setLoading(true)
    expect(isLoading.value).toBe(true)
    setLoading(false)
    expect(isLoading.value).toBe(false)
  })

  it('should set and clear error', () => {
    const { error, hasError, setError, clearError } = useLoading()
    setError('Test error')
    expect(error.value).toBe('Test error')
    expect(hasError.value).toBe(true)
    clearError()
    expect(error.value).toBeNull()
    expect(hasError.value).toBe(false)
  })
})
