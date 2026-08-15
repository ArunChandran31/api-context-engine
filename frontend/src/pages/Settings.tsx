import { useState } from 'react'
import type { Page } from '../utils'
import { CARD, BTN_PRIMARY, BTN_SECONDARY, INPUT_STYLE } from '../utils'

interface Props { navigate: (p: Page) => void }

export default function Settings({ navigate }: Props) {
  const [provider, setProvider] = useState('Groq')
  const [model, setModel] = useState('llama3-8b-8192')
  const [timeout, setTimeout_] = useState('30')
  const [retries, setRetries] = useState('3')
  const [backoff, setBackoff] = useState('2')
  const [guardrails, setGuardrails] = useState(true)
  const [appName, setAppName] = useState('API Context Engine')
  const [logLevel, setLogLevel] = useState('info')
  const [saved, setSaved] = useState(false)

  function save() {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function reset() {
    setProvider('Groq')
    setModel('llama3-8b-8192')
    setTimeout_('30')
    setRetries('3')
    setBackoff('2')
    setGuardrails(true)
    setAppName('API Context Engine')
    setLogLevel('info')
  }

  const labelClass = 'text-[12px] text-[#888] block mb-1.5'
  const sectionTitle = 'text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-4'

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-[26px] font-semibold text-[#1a1a1a]">Settings</h1>
          <p className="text-[14px] text-[#888] mt-0.5">Configure AI provider and application defaults</p>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {/* AI provider */}
        <div style={{ ...CARD, padding: '24px' }}>
          <div className={sectionTitle}>AI provider</div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Provider</label>
              <select
                value={provider}
                onChange={e => setProvider(e.target.value)}
                style={{ ...INPUT_STYLE }}
              >
                <option>Groq</option>
                <option>OpenAI</option>
                <option>Anthropic</option>
                <option>Ollama</option>
              </select>
            </div>

            <div>
              <label className={labelClass}>Model</label>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                style={{ ...INPUT_STYLE, fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}
              >
                <option value="llama3-8b-8192">llama3-8b-8192</option>
                <option value="llama3-70b-8192">llama3-70b-8192</option>
                <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>
                <option value="gemma-7b-it">gemma-7b-it</option>
              </select>
            </div>

            <div>
              <label className={labelClass}>Request timeout (s)</label>
              <input
                type="number"
                value={timeout}
                onChange={e => setTimeout_(e.target.value)}
                style={{ ...INPUT_STYLE }}
                min={5} max={300}
              />
            </div>

            <div>
              <label className={labelClass}>Max retries</label>
              <input
                type="number"
                value={retries}
                onChange={e => setRetries(e.target.value)}
                style={{ ...INPUT_STYLE }}
                min={0} max={10}
              />
            </div>

            <div>
              <label className={labelClass}>Retry backoff (s)</label>
              <input
                type="number"
                value={backoff}
                onChange={e => setBackoff(e.target.value)}
                style={{ ...INPUT_STYLE }}
                min={1} max={30}
              />
            </div>

            <div>
              <label className={labelClass}>Production guardrails</label>
              <button
                onClick={() => setGuardrails(v => !v)}
                className="flex items-center gap-2"
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, marginTop: 2 }}
              >
                <div
                  className="w-10 h-5 rounded-full flex items-center transition-all"
                  style={{
                    background: guardrails ? '#1a1a1a' : 'rgba(0,0,0,0.12)',
                    padding: '2px',
                    justifyContent: guardrails ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div className="w-4 h-4 rounded-full bg-white" style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.2)' }} />
                </div>
                <span className="text-[13px] text-[#555]" style={{ fontFamily: 'Questrial, sans-serif' }}>
                  {guardrails ? 'Enabled' : 'Disabled'}
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Application */}
        <div style={{ ...CARD, padding: '24px' }}>
          <div className={sectionTitle}>Application</div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Application name</label>
              <input
                value={appName}
                onChange={e => setAppName(e.target.value)}
                style={{ ...INPUT_STYLE }}
              />
            </div>

            <div>
              <label className={labelClass}>Log level</label>
              <select
                value={logLevel}
                onChange={e => setLogLevel(e.target.value)}
                style={{ ...INPUT_STYLE, fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}
              >
                <option value="debug">debug</option>
                <option value="info">info</option>
                <option value="warn">warn</option>
                <option value="error">error</option>
              </select>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <button
            style={{ ...BTN_SECONDARY, color: '#b91c1c', borderColor: 'rgba(239,68,68,0.2)', background: 'rgba(239,68,68,0.06)' }}
            onClick={reset}
          >
            Reset to defaults
          </button>
          <button
            style={{ ...BTN_PRIMARY, background: saved ? '#22c55e' : '#1a1a1a', minWidth: 120, justifyContent: 'center' }}
            onClick={save}
          >
            {saved ? (
              <>
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                Saved
              </>
            ) : 'Save settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
