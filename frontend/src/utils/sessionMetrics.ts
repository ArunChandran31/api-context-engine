const AI_QUERY_COUNT_KEY = 'api-context-engine:ai-query-count'

export function getAIQueryCount(): number {
  if (typeof window === 'undefined') {
    return 0
  }

  const value = window.sessionStorage.getItem(
    AI_QUERY_COUNT_KEY,
  )

  if (value === null) {
    return 0
  }

  const count = Number.parseInt(value, 10)

  return Number.isFinite(count) && count >= 0 ? count : 0
}

export function incrementAIQueryCount(): number {
  const nextCount = getAIQueryCount() + 1

  window.sessionStorage.setItem(
    AI_QUERY_COUNT_KEY,
    String(nextCount),
  )

  window.dispatchEvent(new Event('ai-query-count-changed'))

  return nextCount
}
