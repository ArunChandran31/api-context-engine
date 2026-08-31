import { apiRequest } from './client'

export interface DebugRequest {
  question: string
  specification_id: number
  endpoint: string
  status_code: number
  error_message: string
  request_body?: string
  response_body?: string
}

export interface DebugResponse {
  explanation: string
}

export async function debugApiFailure(
  request: DebugRequest,
): Promise<DebugResponse> {
  return apiRequest<DebugResponse>('/api/ai/debug', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}