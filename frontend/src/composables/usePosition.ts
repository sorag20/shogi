import { ref, computed } from 'vue'
import { positionApi, type Position } from '../api'
import { useLoading } from './useLoading'

export function usePosition() {
  const { isLoading, error, setLoading, setError, clearError } = useLoading()
  const position = ref<Position | null>(null)

  const createPosition = async (boardState: any, turn: 'black' | 'white' = 'black') => {
    setLoading(true)
    clearError()
    try {
      const newPosition = await positionApi.create({
        board_state: boardState,
        turn,
      })
      position.value = newPosition
      return newPosition
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create position')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const getPosition = async (id: string) => {
    setLoading(true)
    clearError()
    try {
      const pos = await positionApi.getById(id)
      position.value = pos
      return pos
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get position')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const updatePosition = async (id: string, updates: any) => {
    setLoading(true)
    clearError()
    try {
      const updated = await positionApi.update(id, updates)
      position.value = updated
      return updated
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update position')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const deletePosition = async (id: string) => {
    setLoading(true)
    clearError()
    try {
      await positionApi.delete(id)
      position.value = null
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete position')
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    position,
    isLoading,
    error,
    createPosition,
    getPosition,
    updatePosition,
    deletePosition,
  }
}
