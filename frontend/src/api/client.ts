import { supabase } from '../lib/supabase'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const isFormData = options.body instanceof FormData

  const headers = new Headers(options.headers)

  if (!isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  /*
   * Get the current Supabase session and attach its access token.
   *
   * The backend uses this token to determine the authenticated
   * Supabase user. The frontend never sends a user ID as an
   * ownership value.
   */
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (session?.access_token) {
    headers.set(
      'Authorization',
      `Bearer ${session.access_token}`,
    )
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`

    try {
      const body = await response.json()

      if (typeof body?.detail === 'string') {
        message = body.detail
      } else if (typeof body?.message === 'string') {
        message = body.message
      }
    } catch {
      // Keep the default error message.
    }

    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
