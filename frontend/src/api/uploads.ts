import { apiRequest } from './client'

export interface UploadRAGResponse {
  documents_indexed: number
  chunks_indexed: number
  cache_entries_invalidated: number
}

export interface UploadResponse {
  specification_id: number
  title: string
  version: string | null
  endpoints_created: number
  filename: string
  rag: UploadRAGResponse
}

export async function uploadSpecification(
  file: File,
): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return apiRequest<UploadResponse>('/api/upload', {
    method: 'POST',
    body: formData,
  })
}