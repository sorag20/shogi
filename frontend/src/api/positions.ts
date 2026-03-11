import apiClient from './client'

export interface Position {
  id: string
  board_state: any
  turn: 'black' | 'white'
  metadata?: any
  created_at: string
  updated_at: string
}

export interface CreatePositionRequest {
  board_state: any
  turn: 'black' | 'white'
  metadata?: any
}

export interface UpdatePositionRequest {
  board_state?: any
  turn?: 'black' | 'white'
  metadata?: any
}

export const positionApi = {
  /**
   * Create a new position
   */
  async create(data: CreatePositionRequest): Promise<Position> {
    return apiClient.post<Position>('/api/positions', data)
  },

  /**
   * Get a position by ID
   */
  async getById(id: string): Promise<Position> {
    return apiClient.get<Position>(`/api/positions/${id}`)
  },

  /**
   * Update a position
   */
  async update(id: string, data: UpdatePositionRequest): Promise<Position> {
    return apiClient.put<Position>(`/api/positions/${id}`, data)
  },

  /**
   * Delete a position
   */
  async delete(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/positions/${id}`)
  },
}
