import { useState } from 'react'
import type { Page } from '../utils'
import { CARD, BTN_PRIMARY, MethodBadge } from '../utils'

interface Props { navigate: (p: Page) => void }

type TestStyle = 'jest' | 'pytest' | 'postman' | 'curl'
type TestCategory = 'happy' | 'validation' | 'edge' | 'auth'

interface TestCase {
  id: string
  title: string
  category: TestCategory
  input: string
  expected: string
}

const ENDPOINTS = [
  'GET /pets',
  'POST /pets',
  'GET /pets/{petId}',
  'PUT /pets/{petId}',
  'DELETE /pets/{petId}',
  'POST /store/order',
]

const GENERATED: TestCase[] = [
  {
    id: 't1',
    title: 'Successfully creates a pet with valid payload',
    category: 'happy',
    input: `POST /pets
Content-Type: application/json

{
  "name": "Buddy",
  "status": "available",
  "category": { "id": 1, "name": "Dogs" }
}`,
    expected: `HTTP 201 Created
{
  "id": 42,
  "name": "Buddy",
  "status": "available"
}`,
  },
  {
    id: 't2',
    title: 'Returns 400 when name field is missing',
    category: 'validation',
    input: `POST /pets
Content-Type: application/json

{
  "status": "available"
}`,
    expected: `HTTP 400 Bad Request
{
  "code": 400,
  "message": "Validation Failed: name is required"
}`,
  },
  {
    id: 't3',
    title: 'Returns 400 for invalid status enum value',
    category: 'validation',
    input: `POST /pets
Content-Type: application/json

{
  "name": "Buddy",
  "status": "invalid_status"
}`,
    expected: `HTTP 400 Bad Request
{
  "code": 400,
  "message": "Validation Failed: invalid enum value for status"
}`,
  },
  {
    id: 't4',
    title: 'Handles extremely long name field (edge case)',
    category: 'edge',
    input: `POST /pets
Content-Type: application/json

{
  "name": "${'A'.repeat(255)}",
  "status": "available"
}`,
    expected: `HTTP 400 or 201
Verify max-length constraint is enforced`,
  },
  {
    id: 't5',
    title: 'Returns 401 when Authorization header is missing',
    category: 'auth',
    input: `POST /pets
Content-Type: application/json
# No Authorization header

{
  "name": "Buddy",
  "status": "available"
}`,
    expected: `HTTP 401 Unauthorized
{
  "code": 401,
  "message": "Unauthorized"
}`,
  },
]

const CATEGORY_META: Record<TestCategory, { label: string; color: string; textColor: string }> = {
  happy: { label: 'Happy path', color: '#dcfce7', textColor: '#15803d' },
  validation: { label: 'Validation', color: '#fef3c7', textColor: '#b45309' },
  edge: { label: 'Edge case', color: '#ede9fe', textColor: '#6d28d9' },
  auth: { label: 'Auth', color: '#fee2e2', textColor: '#b91c1c' },
}

function TestCaseRow({ tc }: { tc: TestCase }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const meta = CATEGORY_META[tc.category]

  function copy() {
    navigator.clipboard?.writeText(tc.input + '\n\nExpected:\n' + tc.expected)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-5 py-3.5 text-left hover:bg-black/[0.015] transition-colors"
        style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}
      >
        <span
          className="text-[11px] font-medium px-2 py-0.5 rounded-full flex-shrink-0"
          style={{ background: meta.color, color: meta.textColor }}
        >
          {meta.label}
        </span>
        <span className="text-[14px] text-[#1a1a1a] flex-1 text-left">{tc.title}</span>
        <svg
          width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#aaa" strokeWidth={2} strokeLinecap="round"
          style={{ transform: open ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 200ms', flexShrink: 0 }}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div className="px-5 pb-4 grid grid-cols-2 gap-3">
          <div>
            <div className="text-[11px] text-[#aaa] mb-1.5">Input / request</div>
            <pre
              className="rounded-[12px] p-3 text-[11px] overflow-x-auto leading-relaxed"
              style={{ background: '#f5f5f5', border: '1px solid rgba(0,0,0,0.06)', fontFamily: 'JetBrains Mono, monospace', whiteSpace: 'pre-wrap' }}
            >
              {tc.input}
            </pre>
          </div>
          <div>
            <div className="text-[11px] text-[#aaa] mb-1.5">Expected response</div>
            <pre
              className="rounded-[12px] p-3 text-[11px] overflow-x-auto leading-relaxed"
              style={{ background: '#f5f5f5', border: '1px solid rgba(0,0,0,0.06)', fontFamily: 'JetBrains Mono, monospace', whiteSpace: 'pre-wrap' }}
            >
              {tc.expected}
            </pre>
          </div>
          <div className="col-span-2 flex justify-end">
            <button
              onClick={copy}
              className="text-[12px] px-3 py-1.5 rounded-[10px] text-[#555] transition-colors"
              style={{ background: copied ? '#dcfce7' : 'rgba(0,0,0,0.06)', color: copied ? '#15803d' : '#555', border: 'none', cursor: 'pointer', fontFamily: 'Questrial, sans-serif' }}
            >
              {copied ? 'Copied!' : 'Copy test case'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function TestCases({ navigate }: Props) {
  const [endpoint, setEndpoint] = useState(ENDPOINTS[1])
  const [style, setStyle] = useState<TestStyle>('jest')
  const [categories, setCategories] = useState<TestCategory[]>(['happy', 'validation', 'edge', 'auth'])
  const [generated, setGenerated] = useState(false)
  const [generating, setGenerating] = useState(false)

  function generate() {
    setGenerating(true)
    setTimeout(() => { setGenerating(false); setGenerated(true) }, 1200)
  }

  function toggleCat(cat: TestCategory) {
    setCategories(prev => prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat])
  }

  const filtered = GENERATED.filter(tc => categories.includes(tc.category))

  const [method, path] = endpoint.split(' ')

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-[26px] font-semibold text-[#1a1a1a]">Test Case Generator</h1>
        <p className="text-[14px] text-[#888] mt-0.5">Generate comprehensive test suites from your API schema</p>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {/* Left: controls */}
        <div className="col-span-2">
          <div style={{ ...CARD, padding: '20px' }}>
            <div className="flex flex-col gap-4">
              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">Endpoint</label>
                <select
                  value={endpoint}
                  onChange={e => { setEndpoint(e.target.value); setGenerated(false) }}
                  className="w-full rounded-[12px] text-[13px] text-[#1a1a1a]"
                  style={{ background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(0,0,0,0.1)', padding: '8px 12px', fontFamily: 'JetBrains Mono, monospace', outline: 'none' }}
                >
                  {ENDPOINTS.map(e => <option key={e}>{e}</option>)}
                </select>
              </div>

              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">Test style</label>
                <div className="grid grid-cols-2 gap-1.5">
                  {(['jest', 'pytest', 'postman', 'curl'] as TestStyle[]).map(s => (
                    <button
                      key={s}
                      onClick={() => setStyle(s)}
                      className="py-2 rounded-[10px] text-[13px] capitalize transition-all"
                      style={{
                        background: style === s ? '#1a1a1a' : 'rgba(0,0,0,0.04)',
                        color: style === s ? '#fff' : '#555',
                        border: 'none',
                        cursor: 'pointer',
                        fontFamily: 'Questrial, sans-serif',
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[12px] text-[#888] block mb-2">Generation options</label>
                <div className="flex flex-col gap-2">
                  {(Object.entries(CATEGORY_META) as [TestCategory, typeof CATEGORY_META[TestCategory]][]).map(([cat, meta]) => (
                    <label key={cat} className="flex items-center gap-2.5 cursor-pointer">
                      <div
                        onClick={() => toggleCat(cat)}
                        className="w-4 h-4 rounded-[5px] flex items-center justify-center flex-shrink-0"
                        style={{
                          background: categories.includes(cat) ? '#1a1a1a' : 'rgba(0,0,0,0.08)',
                          border: categories.includes(cat) ? 'none' : '1px solid rgba(0,0,0,0.1)',
                          cursor: 'pointer',
                        }}
                      >
                        {categories.includes(cat) && (
                          <svg width={10} height={10} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={3} strokeLinecap="round">
                            <path d="M20 6L9 17l-5-5" />
                          </svg>
                        )}
                      </div>
                      <span
                        className="text-[11px] px-2 py-0.5 rounded-full font-medium"
                        style={{ background: meta.color, color: meta.textColor }}
                      >
                        {meta.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <button
                style={{ ...BTN_PRIMARY, width: '100%', justifyContent: 'center', opacity: generating ? 0.7 : 1 }}
                onClick={generate}
                disabled={generating}
              >
                {generating ? (
                  <><div className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" /> Generating...</>
                ) : 'Generate test cases'}
              </button>
            </div>
          </div>
        </div>

        {/* Right: results */}
        <div className="col-span-3">
          {!generated && !generating && (
            <div className="flex flex-col items-center justify-center rounded-[20px] text-center" style={{ ...CARD, minHeight: 300 }}>
              <svg width={40} height={40} viewBox="0 0 24 24" fill="none" stroke="#ddd" strokeWidth={1.5} strokeLinecap="round" className="mb-3">
                <path d="M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </svg>
              <div className="text-[14px] text-[#ccc]">Configure and generate<br />to see test cases here</div>
            </div>
          )}

          {generating && (
            <div className="flex flex-col items-center justify-center rounded-[20px]" style={{ ...CARD, minHeight: 300 }}>
              <div className="w-8 h-8 rounded-full border-2 border-black/10 border-t-black/70 animate-spin mb-3" />
              <div className="text-[14px] text-[#888]">Generating test cases...</div>
            </div>
          )}

          {generated && (
            <div style={{ ...CARD, padding: 0, overflow: 'hidden' }}>
              <div className="px-5 py-3.5 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                <div className="flex items-center gap-3">
                  <MethodBadge method={method} />
                  <span className="font-mono text-[13px] text-[#1a1a1a]">{path}</span>
                </div>
                <span className="text-[12px] text-[#aaa]">{filtered.length} test cases · {style}</span>
              </div>

              {filtered.map(tc => <TestCaseRow key={tc.id} tc={tc} />)}

              {filtered.length === 0 && (
                <div className="py-10 text-center text-[13px] text-[#ccc]">
                  No categories selected
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
