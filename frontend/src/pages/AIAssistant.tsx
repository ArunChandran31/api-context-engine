import { useState, useRef, useEffect } from 'react'
import type { Page } from '../utils'
import { CARD, INPUT_STYLE } from '../utils'

interface Props { navigate: (p: Page) => void }

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: { method: string; path: string; spec: string }[]
}

const INITIAL: Message[] = [
  {
    role: 'assistant',
    content: "Hello! I'm your API context assistant. I've indexed your Petstore API, Payment API, and External Users API. Ask me anything about endpoints, schemas, request formats, or authentication.",
  },
]

const DEMO_RESPONSES: Record<string, { content: string; sources?: { method: string; path: string; spec: string }[] }> = {
  default: {
    content: "Based on the indexed API context, here's what I found:\n\nThe endpoint you're asking about supports standard REST operations. The request body should be JSON-encoded with the Content-Type header set to `application/json`. Authentication is required via Bearer token in the Authorization header.\n\nYou can also explore the full schema in the API Explorer for more details.",
    sources: [
      { method: 'POST', path: '/pets', spec: 'Petstore API' },
      { method: 'GET', path: '/pets/{petId}', spec: 'Petstore API' },
    ],
  },
  auth: {
    content: "Authentication uses OAuth 2.0 with the following scopes:\n\n• `read:pets` — Read-only access to pet data\n• `write:pets` — Create, update, and delete pets\n• `admin` — Full administrative access\n\nInclude the token in your Authorization header:\n```\nAuthorization: Bearer <your_token>\n```\n\nTokens expire after 3600 seconds. Use the `/user/login` endpoint to obtain a new token.",
    sources: [
      { method: 'GET', path: '/user/login', spec: 'Petstore API' },
      { method: 'GET', path: '/user/logout', spec: 'Petstore API' },
    ],
  },
}

function SourceTag({ method, path, spec }: { method: string; path: string; spec: string }) {
  const colors: Record<string, { bg: string; text: string }> = {
    GET: { bg: '#dcfce7', text: '#15803d' },
    POST: { bg: '#dbeafe', text: '#1d4ed8' },
    PUT: { bg: '#fef3c7', text: '#b45309' },
    DELETE: { bg: '#fee2e2', text: '#b91c1c' },
    PATCH: { bg: '#ede9fe', text: '#6d28d9' },
  }
  const c = colors[method] ?? { bg: '#f3f4f6', text: '#4b5563' }

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-[10px]" style={{ background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.07)' }}>
      <span className="font-mono text-[11px] font-semibold px-1.5 py-0.5 rounded-full" style={{ background: c.bg, color: c.text }}>{method}</span>
      <span className="font-mono text-[12px] text-[#555]">{path}</span>
      <span className="text-[11px] text-[#aaa]">{spec}</span>
    </div>
  )
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  const lines = msg.content.split('\n')

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mr-3 mt-0.5"
          style={{ background: '#1a1a1a' }}
        >
          <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2} strokeLinecap="round">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z" />
            <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </div>
      )}
      <div className="max-w-[80%]">
        <div
          className="px-4 py-3 rounded-[16px] text-[14px] leading-relaxed"
          style={{
            background: isUser ? '#1a1a1a' : 'rgba(255,255,255,0.8)',
            color: isUser ? '#fff' : '#1a1a1a',
            border: isUser ? 'none' : '1px solid rgba(0,0,0,0.08)',
            backdropFilter: 'blur(8px)',
            borderTopRightRadius: isUser ? 4 : 16,
            borderTopLeftRadius: isUser ? 16 : 4,
          }}
        >
          {lines.map((line, i) => {
            if (line.startsWith('```')) return null
            if (line.match(/^[•\-] /)) {
              return <div key={i} className="flex gap-2 my-0.5"><span style={{ opacity: 0.5 }}>•</span><span>{line.slice(2)}</span></div>
            }
            if (line.includes('`') && !line.startsWith('```')) {
              const parts = line.split(/(`[^`]+`)/)
              return (
                <p key={i} className="mb-1">
                  {parts.map((p, j) => p.startsWith('`') && p.endsWith('`')
                    ? <code key={j} className="font-mono text-[12px] px-1 rounded" style={{ background: isUser ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.06)' }}>{p.slice(1,-1)}</code>
                    : <span key={j}>{p}</span>
                  )}
                </p>
              )
            }
            return line ? <p key={i} className="mb-1">{line}</p> : <div key={i} className="h-1" />
          })}
        </div>

        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-2">
            <div className="text-[11px] text-[#aaa] mb-1 pl-1">Sources</div>
            <div className="flex flex-wrap gap-1.5">
              {msg.sources.map((s, i) => <SourceTag key={i} {...s} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AIAssistant({ navigate }: Props) {
  const [messages, setMessages] = useState<Message[]>(INITIAL)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState('Petstore API')
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function send() {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: q }])
    setLoading(true)

    setTimeout(() => {
      const key = q.toLowerCase().includes('auth') ? 'auth' : 'default'
      const res = DEMO_RESPONSES[key]
      setMessages(prev => [...prev, { role: 'assistant', ...res }])
      setLoading(false)
    }, 1200)
  }

  function clear() {
    setMessages(INITIAL)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-[26px] font-semibold text-[#1a1a1a]">AI Assistant</h1>
          <p className="text-[14px] text-[#888] mt-0.5">Ask questions about your indexed APIs</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Context selector */}
          <select
            value={context}
            onChange={e => setContext(e.target.value)}
            style={{ ...INPUT_STYLE, width: 'auto', borderRadius: '20px', fontSize: 13, padding: '6px 14px' }}
          >
            <option>Petstore API</option>
            <option>Payment API</option>
            <option>External Users API</option>
            <option>All APIs</option>
          </select>
          <button
            onClick={clear}
            className="text-[13px] text-[#888] hover:text-[#1a1a1a] transition-colors px-3 py-1.5 rounded-[12px]"
            style={{ background: 'rgba(255,255,255,0.6)', border: '1px solid rgba(0,0,0,0.08)', cursor: 'pointer', fontFamily: 'Questrial, sans-serif' }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Context badge */}
      <div className="mb-3 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full" style={{ background: '#22c55e' }} />
        <span className="text-[12px] text-[#888]">Context: <span className="text-[#555] font-medium">{context}</span></span>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto py-2"
        style={{ scrollbarWidth: 'none' }}
      >
        {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}

        {loading && (
          <div className="flex gap-3 mb-4">
            <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: '#1a1a1a' }}>
              <div className="w-3 h-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            </div>
            <div className="px-4 py-3 rounded-[16px] rounded-tl-[4px] text-[14px]"
              style={{ background: 'rgba(255,255,255,0.8)', border: '1px solid rgba(0,0,0,0.08)' }}>
              <div className="flex gap-1">
                {[0,1,2].map(i => (
                  <div key={i} className="w-1.5 h-1.5 rounded-full bg-[#bbb] animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div
        className="flex items-end gap-2 mt-3 p-2 rounded-[20px]"
        style={{ background: 'rgba(255,255,255,0.72)', border: '1px solid rgba(255,255,255,0.9)', backdropFilter: 'blur(12px)', boxShadow: '0 2px 16px rgba(0,0,0,0.06)' }}
      >
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          placeholder="Ask about endpoints, schemas, authentication..."
          rows={1}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            resize: 'none',
            fontFamily: 'Questrial, sans-serif',
            fontSize: 14,
            color: '#1a1a1a',
            padding: '8px 12px',
            lineHeight: 1.5,
            maxHeight: 120,
            overflowY: 'auto',
          }}
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading}
          className="flex items-center justify-center rounded-[14px] flex-shrink-0"
          style={{
            width: 36, height: 36,
            background: input.trim() && !loading ? '#1a1a1a' : 'rgba(0,0,0,0.08)',
            border: 'none',
            cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
            color: input.trim() && !loading ? '#fff' : '#ccc',
          }}
        >
          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
