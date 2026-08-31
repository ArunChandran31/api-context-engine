import { apiRequest } from './client'

export type TestStyle =
  | 'jest'
  | 'pytest'
  | 'postman'
  | 'curl'

export type TestCategory =
  | 'happy'
  | 'validation'
  | 'edge'
  | 'auth'
  | 'errors'

export interface GeneratedTestCase {
  category: string
  description: string
}

export interface TestCaseGenerationResponse {
  test_cases: GeneratedTestCase[]
}

export async function generateTestCases(
  question: string,
  specificationId: number,
  testStyle: TestStyle,
  categories: TestCategory[],
): Promise<TestCaseGenerationResponse> {
  return apiRequest<TestCaseGenerationResponse>(
    '/api/ai/test-cases',
    {
      method: 'POST',
      body: JSON.stringify({
        question,
        specification_id: specificationId,
        test_style: testStyle,
        categories,
      }),
    },
  )
}