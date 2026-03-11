import apiClient from './client'

export interface EvaluationRequest {
  position: {
    board: any
    turn: 'black' | 'white'
  }
}

export interface EvaluationResponse {
  evaluation: number
  best_move?: string
  pv?: string[]
  computed_at: string
}

export const evaluationApi = {
  /**
   * Get evaluation for a position
   */
  async evaluate(position: EvaluationRequest['position']): Promise<EvaluationResponse> {
    return apiClient.post<EvaluationResponse>('/api/evaluate', { position })
  },
}
