import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios'

interface ApiError {
  error: string
  message: string
  timestamp: string
}

interface ApiResponse<T> {
  data: T
  status: number
}

class ApiClient {
  private client: AxiosInstance
  private baseURL: string

  constructor(baseURL?: string) {
    this.baseURL = baseURL || import.meta.env.VITE_API_URL || 'http://localhost:5000'

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response) {
          // Server responded with error status
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          // Request made but no response
          console.error('No response from server:', error.request)
        } else {
          // Error in request setup
          console.error('Request error:', error.message)
        }
        return Promise.reject(error)
      }
    )
  }

  async get<T>(url: string, config?: any): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.get(url, config)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async post<T>(url: string, data?: any, config?: any): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.post(url, data, config)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async put<T>(url: string, data?: any, config?: any): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.put(url, data, config)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async delete<T>(url: string, config?: any): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.delete(url, config)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  private handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError | undefined
      if (apiError) {
        return new Error(`${apiError.error}: ${apiError.message}`)
      }
      return new Error(error.message)
    }
    return error
  }
}

export default new ApiClient()
