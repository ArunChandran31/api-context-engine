import { useState } from 'react'
import type { Page } from '../utils'
import { CARD, BTN_PRIMARY, INPUT_STYLE } from '../utils'

interface Props { navigate: (p: Page) => void }

const DEMO_DIAGNOSIS = {
  likelyCause: 'Missing required field `name` in request body. The Petstore API schema mandates this field for POST /pets operations.',
  suggestedFix: 'Ensure the request body includes the `name` field with a non-empty string value. Additionally, verify that the `Content-Type: application/json` header is set.',
  details: [
    'Required field `name` is absent from the request body',
    'The `status` field value "unknown" is not in the allowed enum: [available, pending, sold]',
    'Provide a non-empty string value satisfying the required schema',
  ],
}

function Code({ children }: { children: string }) {
  return (
    <pre
      className="rounded-[12px] p-3 text-[12px] overflow-x-auto leading-relaxed"
      style={{ background: '#f5f5f5', border: '1px solid rgba(0,0,0,0.06)', fontFamily: 'JetBrains Mono, monospace' }}
    >
      {children}
    </pre>
  )
}

export default function DebugAssistant({ navigate }: Props) {
  const [endpoint, setEndpoint] = useState('POST /pets')
  const [status, setStatus] = useState('400')
  const [errorMsg, setErrorMsg] = useState('Bad Request — validation failed')
  const [requestBody, setRequestBody] = useState(`{
  "status": "unknown",
  "category": { "id": 1, "name": "Dogs" }
}`)
  const [responseBody, setResponseBody] = useState(`{
  "code": 400,
  "type": "error",
  "message": "Validation Failed: name is required"
}`)
  const [analyzed, setAnalyzed] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)

  function analyze() {
    setAnalyzing(true)
    setTimeout(() => {
      setAnalyzing(false)
      setAnalyzed(true)
    }, 1400)
  }

  const statusColors: Record<string, { bg: string; text: string }> = {
    '2': { bg: '#dcfce7', text: '#15803d' },
    '4': { bg: '#fef3c7', text: '#b45309' },
    '5': { bg: '#fee2e2', text: '#b91c1c' },
  }
  const sc = statusColors[status[0]] ?? { bg: '#f3f4f6', text: '#4b5563' }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-[26px] font-semibold text-[#1a1a1a]">Debug Assistant</h1>
        <p className="text-[14px] text-[#888] mt-0.5">Diagnose API failures with AI-powered analysis</p>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {/* Left: input form */}
        <div className="col-span-2 flex flex-col gap-3">
          <div style={{ ...CARD, padding: '20px' }}>
            <div className="text-[13px] font-medium text-[#555] mb-4">Failure details</div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">Endpoint</label>
                <input style={INPUT_STYLE} value={endpoint} onChange={e => setEndpoint(e.target.value)} placeholder="POST /pets" />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[12px] text-[#888] block mb-1.5">HTTP Status</label>
                  <input style={INPUT_STYLE} value={status} onChange={e => setStatus(e.target.value)} placeholder="400" />
                </div>
                <div>
                  <label className="text-[12px] text-[#888] block mb-1.5">Status badge</label>
                  <div className="flex items-center h-[36px]">
                    <span className="px-3 py-1 rounded-full text-[13px] font-semibold font-mono" style={{ background: sc.bg, color: sc.text }}>{status}</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">Error message</label>
                <input style={INPUT_STYLE} value={errorMsg} onChange={e => setErrorMsg(e.target.value)} />
              </div>

              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">Request body</label>
                <textarea
                  value={requestBody}
                  onChange={e => setRequestBody(e.target.value)}
                  rows={5}
                  style={{ ...INPUT_STYLE, fontFamily: 'JetBrains Mono, monospace', fontSize: 12, resize: 'vertical', lineHeight: 1.5 }}
                />
              </div>

              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">Response / stack trace</label>
                <textarea
                  value={responseBody}
                  onChange={e => setResponseBody(e.target.value)}
                  rows={5}
                  style={{ ...INPUT_STYLE, fontFamily: 'JetBrains Mono, monospace', fontSize: 12, resize: 'vertical', lineHeight: 1.5 }}
                />
              </div>
            </div>

            <button
              style={{ ...BTN_PRIMARY, marginTop: 16, width: '100%', justifyContent: 'center', opacity: analyzing ? 0.7 : 1 }}
              onClick={analyze}
              disabled={analyzing}
            >
              {analyzing ? (
                <>
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
                    <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0 0h18" />
                  </svg>
                  Analyze failure
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: diagnosis */}
        <div className="col-span-3 flex flex-col gap-3">
          {!analyzed && !analyzing && (
            <div
              className="flex flex-col items-center justify-center rounded-[20px] text-center"
              style={{ ...CARD, minHeight: 300 }}
            >
              <svg width={40} height={40} viewBox="0 0 24 24" fill="none" stroke="#ddd" strokeWidth={1.5} strokeLinecap="round" className="mb-3">
                <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0 0h18" />
              </svg>
              <div className="text-[14px] text-[#ccc]">Fill in the failure details and click<br />Analyze failure to get a diagnosis</div>
            </div>
          )}

          {analyzing && (
            <div className="flex flex-col items-center justify-center rounded-[20px]" style={{ ...CARD, minHeight: 300 }}>
              <div className="w-8 h-8 rounded-full border-2 border-black/10 border-t-black/70 animate-spin mb-3" />
              <div className="text-[14px] text-[#888]">Analyzing failure...</div>
            </div>
          )}

          {analyzed && (
            <>
              {/* Diagnosis */}
              <div style={{ ...CARD, padding: '20px' }}>
                <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">Diagnosis</div>

                <div className="mb-4">
                  <div className="text-[12px] text-[#aaa] mb-1.5">Likely cause</div>
                  <div className="text-[14px] text-[#1a1a1a] leading-relaxed">{DEMO_DIAGNOSIS.likelyCause}</div>
                </div>

                <div className="mb-4">
                  <div className="text-[12px] text-[#aaa] mb-1.5">Suggested fix</div>
                  <div className="text-[14px] text-[#555] leading-relaxed">{DEMO_DIAGNOSIS.suggestedFix}</div>
                </div>

                <div>
                  <div className="text-[12px] text-[#aaa] mb-1.5">Details</div>
                  <div className="flex flex-col gap-1.5">
                    {DEMO_DIAGNOSIS.details.map((d, i) => (
                      <div key={i} className="flex items-start gap-2 text-[13px] text-[#555]">
                        <span className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: '#f59e0b' }} />
                        {d}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Example fix */}
              <div style={{ ...CARD, padding: '16px 20px' }}>
                <div className="text-[12px] text-[#aaa] mb-2">Corrected request body</div>
                <Code>{`{
  "name": "Buddy",
  "status": "available",
  "category": { "id": 1, "name": "Dogs" }
}`}</Code>
              </div>

              {/* Suggested actions */}
              <div style={{ ...CARD, padding: '16px 20px' }}>
                <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">Suggested actions</div>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => navigate('endpoint')}
                    className="text-[13px] px-4 py-2 rounded-[12px] text-[#1a1a1a]"
                    style={{ background: 'rgba(0,0,0,0.06)', border: 'none', cursor: 'pointer', fontFamily: 'Questrial, sans-serif' }}
                  >
                    Open endpoint
                  </button>
                  <button
                    onClick={() => navigate('assistant')}
                    className="text-[13px] px-4 py-2 rounded-[12px] text-[#2563eb]"
                    style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', cursor: 'pointer', fontFamily: 'Questrial, sans-serif' }}
                  >
                    Ask AI about this
                  </button>
                  <button
                    className="text-[13px] px-4 py-2 rounded-[12px] text-[#555]"
                    style={{ background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.08)', cursor: 'pointer', fontFamily: 'Questrial, sans-serif' }}
                    onClick={() => navigator.clipboard?.writeText(DEMO_DIAGNOSIS.likelyCause + '\n\n' + DEMO_DIAGNOSIS.suggestedFix)}
                  >
                    Copy diagnosis
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
