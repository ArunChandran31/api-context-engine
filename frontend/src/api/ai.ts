import { apiRequest } from './client'

export interface QuestionSource {
  specification_id: number
  endpoint_id: number
  method: string
  path: string
  operation_id: string | null
}

export interface QuestionResponse {
  answer: string
  sources: QuestionSource[]
}

export async function askQuestion(
  question: string,
  specificationId: number,
): Promise<QuestionResponse> {
  return apiRequest<QuestionResponse>('/api/ai/question', {
    method: 'POST',
    body: JSON.stringify({
      question,
      specification_id: specificationId,
    }),
  })
}