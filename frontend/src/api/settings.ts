import { apiRequest } from './client'

export type AIProvider = 'deterministic' | 'groq' | 'gemini'

export interface AISettings {
  provider: AIProvider
  model: string
  timeout_seconds: number
  max_retries: number
  retry_backoff_seconds: number
  fallback_enabled: boolean
  fallback_provider: AIProvider
}

export interface AISettingsUpdate {
  provider: AIProvider
  model?: string
  timeout_seconds: number
  max_retries: number
  retry_backoff_seconds: number
  fallback_enabled: boolean
  fallback_provider: AIProvider
}

export async function getAISettings(): Promise<AISettings> {
  return apiRequest<AISettings>('/api/settings/ai')
}

export async function updateAISettings(
  settings: AISettingsUpdate,
): Promise<AISettings> {
  return apiRequest<AISettings>('/api/settings/ai', {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
}
