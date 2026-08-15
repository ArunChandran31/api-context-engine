export type Page =
  | 'dashboard'
  | 'upload'
  | 'explorer'
  | 'endpoint'
  | 'assistant'
  | 'debug'
  | 'tests'
  | 'status'
  | 'settings'

export interface NavContextType {
  navigate: (page: Page, data?: unknown) => void
  current: Page
}

export function methodColors(method: string): { bg: string; text: string; border: string } {
  switch (method.toUpperCase()) {
    case 'GET':
      return { bg: '#dcfce7', text: '#15803d', border: '#86efac' }
    case 'POST':
      return { bg: '#dbeafe', text: '#1d4ed8', border: '#93c5fd' }
    case 'PUT':
      return { bg: '#fef3c7', text: '#b45309', border: '#fcd34d' }
    case 'PATCH':
      return { bg: '#ede9fe', text: '#6d28d9', border: '#c4b5fd' }
    case 'DELETE':
      return { bg: '#fee2e2', text: '#b91c1c', border: '#fca5a5' }
    default:
      return { bg: '#f3f4f6', text: '#4b5563', border: '#d1d5db' }
  }
}

export function MethodBadge({ method }: { method: string }) {
  const c = methodColors(method)
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium font-mono"
      style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}
    >
      {method.toUpperCase()}
    </span>
  )
}

export const CARD = {
  background: 'rgba(255,255,255,0.72)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.85)',
  borderRadius: '20px',
  boxShadow: '0 2px 16px rgba(0,0,0,0.06)',
} as const

export const GLASS = {
  background: 'rgba(255,255,255,0.65)',
  backdropFilter: 'blur(24px)',
  WebkitBackdropFilter: 'blur(24px)',
  border: '1px solid rgba(255,255,255,0.85)',
  borderRadius: '20px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
} as const

export const INPUT_STYLE: React.CSSProperties = {
  borderRadius: '12px',
  border: '1px solid rgba(0,0,0,0.1)',
  background: 'rgba(255,255,255,0.7)',
  padding: '8px 14px',
  fontSize: '14px',
  outline: 'none',
  width: '100%',
  fontFamily: 'Questrial, sans-serif',
}

export const BTN_PRIMARY: React.CSSProperties = {
  background: '#1a1a1a',
  color: '#fff',
  borderRadius: '20px',
  padding: '8px 20px',
  fontSize: '14px',
  fontFamily: 'Questrial, sans-serif',
  border: 'none',
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '6px',
  whiteSpace: 'nowrap' as const,
}

export const BTN_SECONDARY: React.CSSProperties = {
  background: 'rgba(255,255,255,0.6)',
  color: '#1a1a1a',
  borderRadius: '20px',
  padding: '8px 20px',
  fontSize: '14px',
  fontFamily: 'Questrial, sans-serif',
  border: '1px solid rgba(0,0,0,0.1)',
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '6px',
  whiteSpace: 'nowrap' as const,
}

export const BTN_GHOST: React.CSSProperties = {
  background: 'transparent',
  color: '#555',
  borderRadius: '20px',
  padding: '8px 16px',
  fontSize: '14px',
  fontFamily: 'Questrial, sans-serif',
  border: 'none',
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '6px',
}
