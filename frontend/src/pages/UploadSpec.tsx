import { useState, useRef } from 'react'
import type { Page } from '../utils'
import { CARD, BTN_PRIMARY, BTN_SECONDARY, INPUT_STYLE } from '../utils'

interface Props { navigate: (p: Page) => void }

type InputMode = 'file' | 'url'
type UploadStep = 'idle' | 'validating' | 'parsing' | 'indexing' | 'ready' | 'error'

const STEPS = [
  { id: 'select', label: 'Select file or URL' },
  { id: 'validate', label: 'Validate specification' },
  { id: 'parse', label: 'Parse endpoints and schemas' },
  { id: 'index', label: 'Index API context' },
  { id: 'ready', label: 'Ready to explore' },
]

function StepRow({ label, state }: { label: string; state: 'done' | 'active' | 'pending' }) {
  return (
    <div className="flex items-center gap-3 py-2.5">
      <div
        className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
        style={{
          background: state === 'done' ? '#22c55e' : state === 'active' ? '#1a1a1a' : 'rgba(0,0,0,0.08)',
        }}
      >
        {state === 'done' && (
          <svg width={11} height={11} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={3} strokeLinecap="round">
            <path d="M20 6L9 17l-5-5" />
          </svg>
        )}
        {state === 'active' && (
          <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
        )}
      </div>
      <span
        className="text-[13px]"
        style={{ color: state === 'pending' ? '#aaa' : '#1a1a1a', fontWeight: state === 'active' ? 600 : 400 }}
      >
        {label}
      </span>
    </div>
  )
}

export default function UploadSpec({ navigate }: Props) {
  const [mode, setMode] = useState<InputMode>('file')
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [url, setUrl] = useState('')
  const [uploadStep, setUploadStep] = useState<UploadStep>('idle')
  const fileRef = useRef<HTMLInputElement>(null)

  const hasInput = mode === 'file' ? !!file : url.trim().length > 0

  function simulate() {
    if (!hasInput) return
    const steps: UploadStep[] = ['validating', 'parsing', 'indexing', 'ready']
    let i = 0
    setUploadStep('validating')
    const tick = () => {
      i++
      if (i < steps.length) {
        setTimeout(() => { setUploadStep(steps[i]); tick() }, 900)
      }
    }
    setTimeout(tick, 900)
  }

  function getStepState(idx: number): 'done' | 'active' | 'pending' {
    const order: UploadStep[] = ['idle', 'validating', 'parsing', 'indexing', 'ready']
    const cur = order.indexOf(uploadStep)
    if (cur === 0) return idx === 0 ? 'active' : 'pending'
    if (idx < cur) return 'done'
    if (idx === cur) return 'active'
    return 'pending'
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-[26px] font-semibold text-[#1a1a1a]">Upload API Specification</h1>
          <p className="text-[14px] text-[#888] mt-0.5">Index your OpenAPI or Swagger specification</p>
        </div>
        <button style={BTN_SECONDARY} onClick={() => navigate('dashboard')}>
          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back
        </button>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {/* Left: input area */}
        <div className="col-span-3 flex flex-col gap-3">
          <div style={CARD}>
            <div className="p-5">
              <div className="text-[13px] font-medium text-[#555] mb-3">Choose an input</div>

              {/* Mode toggle */}
              <div className="flex gap-1 mb-4 p-1 rounded-[14px]" style={{ background: 'rgba(0,0,0,0.05)', width: 'fit-content' }}>
                {(['file', 'url'] as InputMode[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className="px-4 py-1.5 rounded-[11px] text-[13px] transition-all"
                    style={{
                      background: mode === m ? 'rgba(255,255,255,0.9)' : 'transparent',
                      color: mode === m ? '#1a1a1a' : '#888',
                      border: 'none',
                      cursor: 'pointer',
                      fontFamily: 'Questrial, sans-serif',
                      boxShadow: mode === m ? '0 1px 4px rgba(0,0,0,0.08)' : 'none',
                    }}
                  >
                    {m === 'file' ? 'Upload file' : 'URL'}
                  </button>
                ))}
              </div>

              {mode === 'file' ? (
                <>
                  {/* Drop zone */}
                  <div
                    onClick={() => fileRef.current?.click()}
                    onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={(e) => {
                      e.preventDefault()
                      setDragging(false)
                      const f = e.dataTransfer.files[0]
                      if (f) setFile(f)
                    }}
                    className="flex flex-col items-center justify-center rounded-[16px] cursor-pointer transition-all"
                    style={{
                      border: `2px dashed ${dragging ? '#1a1a1a' : 'rgba(0,0,0,0.12)'}`,
                      background: dragging ? 'rgba(0,0,0,0.04)' : 'rgba(0,0,0,0.02)',
                      minHeight: 180,
                      padding: 32,
                    }}
                  >
                    <svg width={36} height={36} viewBox="0 0 24 24" fill="none" stroke="#ccc" strokeWidth={1.5} strokeLinecap="round" className="mb-3">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                    </svg>
                    {file ? (
                      <div className="text-center">
                        <div className="text-[14px] font-medium text-[#1a1a1a]">{file.name}</div>
                        <div className="text-[12px] text-[#888] mt-1">{(file.size / 1024).toFixed(1)} KB</div>
                      </div>
                    ) : (
                      <div className="text-center">
                        <div className="text-[14px] text-[#555]">Drop your API specification here</div>
                        <div className="text-[12px] text-[#aaa] mt-1">or click to browse</div>
                      </div>
                    )}
                    <div className="flex gap-2 mt-3">
                      {['JSON', 'YAML'].map((fmt) => (
                        <span key={fmt} className="px-2 py-0.5 rounded-full text-[11px]" style={{ background: 'rgba(0,0,0,0.06)', color: '#666' }}>
                          {fmt}
                        </span>
                      ))}
                    </div>
                  </div>
                  <input ref={fileRef} type="file" accept=".json,.yaml,.yml" className="hidden" onChange={e => e.target.files?.[0] && setFile(e.target.files[0])} />

                  {/* OR divider */}
                  <div className="flex items-center gap-3 my-3">
                    <div className="flex-1 h-px" style={{ background: 'rgba(0,0,0,0.08)' }} />
                    <span className="text-[12px] text-[#aaa]">or</span>
                    <div className="flex-1 h-px" style={{ background: 'rgba(0,0,0,0.08)' }} />
                  </div>

                  {/* URL input */}
                  <div>
                    <label className="text-[12px] text-[#888] block mb-1.5">Specification URL</label>
                    <input
                      style={INPUT_STYLE}
                      placeholder="https://api.example.com/openapi.json"
                      value={url}
                      onChange={e => setUrl(e.target.value)}
                    />
                  </div>
                </>
              ) : (
                <div>
                  <label className="text-[12px] text-[#888] block mb-1.5">Specification URL</label>
                  <input
                    style={{ ...INPUT_STYLE, borderRadius: '14px' }}
                    placeholder="https://api.example.com/openapi.json"
                    value={url}
                    onChange={e => setUrl(e.target.value)}
                  />
                  <div className="text-[12px] text-[#aaa] mt-2">Supports OpenAPI 3.x and Swagger 2.0</div>
                </div>
              )}
            </div>

            <div className="px-5 pb-5 flex gap-2">
              <button
                style={{ ...BTN_PRIMARY, opacity: hasInput ? 1 : 0.4, cursor: hasInput ? 'pointer' : 'not-allowed' }}
                onClick={simulate}
                disabled={!hasInput}
              >
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
                  <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0 0h18" />
                </svg>
                Analyze specification
              </button>
              {uploadStep === 'ready' && (
                <button style={BTN_SECONDARY} onClick={() => navigate('explorer')}>
                  Explore APIs →
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right: upload flow steps */}
        <div className="col-span-2">
          <div style={{ ...CARD, padding: '20px 24px' }}>
            <div className="text-[13px] font-medium text-[#555] mb-4">Upload flow</div>
            <div className="flex flex-col divide-y" style={{ borderTop: '1px solid rgba(0,0,0,0.06)', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
              {STEPS.map((step, i) => (
                <StepRow key={step.id} label={step.label} state={getStepState(i)} />
              ))}
            </div>

            {uploadStep === 'ready' && (
              <div className="mt-4 rounded-[14px] p-3" style={{ background: '#dcfce7', border: '1px solid #86efac' }}>
                <div className="text-[13px] font-semibold text-[#15803d]">Specification indexed</div>
                <div className="text-[12px] text-[#16a34a] mt-0.5">42 endpoints discovered and ready to explore</div>
              </div>
            )}

            {uploadStep === 'idle' && (
              <div className="mt-4 text-[12px] text-[#aaa]">
                Upload a file or enter a URL, then click Analyze to begin.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
