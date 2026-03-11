import apiClient from './client'

export interface KifuMetadata {
  black_player?: string
  white_player?: string
  game_date?: string
  result?: string
}

export interface Move {
  id: string
  kifu_id: string
  move_number: number
  notation: string
  from_square?: string
  to_square?: string
  piece_type?: string
  is_promotion: boolean
  is_drop: boolean
  comment?: string
  position_after?: any
  created_at: string
}

export interface Kifu {
  id: string
  black_player?: string
  white_player?: string
  game_date?: string
  result?: string
  moves?: Move[]
  created_at: string
  updated_at: string
}

export interface UploadKifuResponse {
  id: string
  metadata: KifuMetadata
  moves: Move[]
}

export const kifuApi = {
  /**
   * Upload and parse a KIF file
   */
  async upload(file: File): Promise<UploadKifuResponse> {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<UploadKifuResponse>('/api/kif/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  /**
   * Get a kifu by ID
   */
  async getById(id: string): Promise<Kifu> {
    return apiClient.get<Kifu>(`/api/kif/${id}`)
  },

  /**
   * Get a specific move's position
   */
  async getMovePosition(id: string, moveNumber: number): Promise<any> {
    return apiClient.get<any>(`/api/kif/${id}/moves/${moveNumber}`)
  },
}
