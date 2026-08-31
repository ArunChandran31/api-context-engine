import { apiRequest } from './client'

export interface HealthService {
  status: 'healthy' | 'degraded' | 'error' | 'configured'
  message?: string
  type?: string
  records?: number
  dimension?: number
  provider?: string
  model?: string
}

export interface HealthResponse {
  status: 'healthy' | 'degraded'
  service: string
  version: string
  services: {
    database: HealthService
    redis: HealthService
    vector_store: HealthService
    llm: HealthService
  }
}

export async function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/health/')
}
