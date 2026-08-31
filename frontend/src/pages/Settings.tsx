import { useEffect, useState } from 'react'
import type { Page } from '../utils'
import { CARD, BTN_PRIMARY, BTN_SECONDARY, INPUT_STYLE } from '../utils'
import {
  getAISettings,
  updateAISettings,
  type AIProvider,
  type AISettings,
} from '../api/settings'

interface Props {
  navigate: (p: Page) => void
}

const MODEL_OPTIONS: Record<AIProvider, string[]> = {
  deterministic: ['deterministic'],
  groq: [
    'openai/gpt-oss-20b',
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
  ],
  gemini: [
    'gemini-3.6-flash',
  ],
}

const DEFAULT_SETTINGS: AISettings = {
  provider: 'groq',
  model: 'openai/gpt-oss-20b',
  timeout_seconds: 60,
  max_retries: 2,
  retry_backoff_seconds: 1,
  fallback_enabled: true,
  fallback_provider: 'gemini',
}

export default function Settings({ navigate: _navigate }: Props) {
  const [settings, setSettings] = useState<AISettings>(DEFAULT_SETTINGS)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Existing application settings UI.
  // These are still local because the current backend
  // settings API only exposes AI configuration.
  const [guardrails, setGuardrails] = useState(true)
  const [appName, setAppName] = useState('API Context Engine')
  const [logLevel, setLogLevel] = useState('info')

  /*
   * Load the effective AI settings from the backend
   * when the Settings page is opened.
   */
  useEffect(() => {
    let mounted = true

    async function loadSettings() {
      try {
        setLoading(true)
        setError(null)

        const current = await getAISettings()

        if (mounted) {
          setSettings(current)
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Failed to load AI settings.',
          )
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    loadSettings()

    return () => {
      mounted = false
    }
  }, [])

  function updateSetting<K extends keyof AISettings>(
    key: K,
    value: AISettings[K],
  ) {
    setSettings(current => ({
      ...current,
      [key]: value,
    }))

    setSaved(false)
    setError(null)
  }

  /*
   * Change the provider and automatically select
   * the first valid model for that provider.
   *
   * Also prevent the fallback provider from becoming
   * identical to the primary provider.
   */
  function handleProviderChange(provider: AIProvider) {
    const model = MODEL_OPTIONS[provider][0]

    setSettings(current => {
      let fallbackProvider = current.fallback_provider

      if (fallbackProvider === provider) {
        if (provider === 'groq') {
          fallbackProvider = 'gemini'
        } else if (provider === 'gemini') {
          fallbackProvider = 'groq'
        } else {
          fallbackProvider = 'gemini'
        }
      }

      return {
        ...current,
        provider,
        model,
        fallback_provider: fallbackProvider,
      }
    })

    setSaved(false)
    setError(null)
  }

  /*
   * Save the current AI configuration to the backend.
   */
  async function save() {
    if (
      settings.fallback_enabled &&
      settings.provider === settings.fallback_provider
    ) {
      setError(
        'Fallback provider must be different from the primary provider.',
      )
      return
    }

    try {
      setSaving(true)
      setSaved(false)
      setError(null)

      const updated = await updateAISettings({
        provider: settings.provider,
        model: settings.model,
        timeout_seconds: settings.timeout_seconds,
        max_retries: settings.max_retries,
        retry_backoff_seconds: settings.retry_backoff_seconds,
        fallback_enabled: settings.fallback_enabled,
        fallback_provider: settings.fallback_provider,
      })

      setSettings(updated)
      setSaved(true)

      window.setTimeout(() => {
        setSaved(false)
      }, 2000)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to save AI settings.',
      )
    } finally {
      setSaving(false)
    }
  }

  /*
   * Reset the form to the application's backend defaults.
   *
   * This only changes the form until Save is clicked.
   */
  function reset() {
    setSettings(DEFAULT_SETTINGS)
    setSaved(false)
    setError(null)
  }

  const labelClass = 'text-[12px] text-[#888] block mb-1.5'

  const sectionTitle =
    'text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-4'

  const availableModels = MODEL_OPTIONS[settings.provider]

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-[26px] font-semibold text-[#1a1a1a]">
            Settings
          </h1>

          <p className="text-[14px] text-[#888] mt-0.5">
            Configure AI provider and application defaults
          </p>
        </div>
      </div>

      {loading ? (
        <div
          style={{
            ...CARD,
            padding: '24px',
          }}
        >
          <p className="text-[14px] text-[#888]">
            Loading AI settings...
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {/* AI provider */}
          <div style={{ ...CARD, padding: '24px' }}>
            <div className={sectionTitle}>AI provider</div>

            <div className="grid grid-cols-2 gap-4">
              {/* Provider */}
              <div>
                <label className={labelClass}>Provider</label>

                <select
                  value={settings.provider}
                  onChange={e =>
                    handleProviderChange(
                      e.target.value as AIProvider,
                    )
                  }
                  style={{ ...INPUT_STYLE }}
                  disabled={saving}
                >
                  <option value="groq">Groq</option>
                  <option value="gemini">Gemini</option>
                  <option value="deterministic">
                    Deterministic
                  </option>
                </select>
              </div>

              {/* Model */}
              <div>
                <label className={labelClass}>Model</label>

                <select
                  value={settings.model}
                  onChange={e =>
                    updateSetting('model', e.target.value)
                  }
                  style={{
                    ...INPUT_STYLE,
                    fontFamily:
                      'JetBrains Mono, monospace',
                    fontSize: 12,
                  }}
                  disabled={saving}
                >
                  {availableModels.map(model => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>

              {/* Timeout */}
              <div>
                <label className={labelClass}>
                  Request timeout (s)
                </label>

                <input
                  type="number"
                  value={settings.timeout_seconds}
                  onChange={e =>
                    updateSetting(
                      'timeout_seconds',
                      Number(e.target.value),
                    )
                  }
                  style={{ ...INPUT_STYLE }}
                  min={1}
                  max={300}
                  disabled={saving}
                />
              </div>

              {/* Max retries */}
              <div>
                <label className={labelClass}>
                  Max retries
                </label>

                <input
                  type="number"
                  value={settings.max_retries}
                  onChange={e =>
                    updateSetting(
                      'max_retries',
                      Number(e.target.value),
                    )
                  }
                  style={{ ...INPUT_STYLE }}
                  min={0}
                  max={10}
                  disabled={saving}
                />
              </div>

              {/* Retry backoff */}
              <div>
                <label className={labelClass}>
                  Retry backoff (s)
                </label>

                <input
                  type="number"
                  value={settings.retry_backoff_seconds}
                  onChange={e =>
                    updateSetting(
                      'retry_backoff_seconds',
                      Number(e.target.value),
                    )
                  }
                  style={{ ...INPUT_STYLE }}
                  min={0.1}
                  max={30}
                  step={0.1}
                  disabled={saving}
                />
              </div>

              {/* Production guardrails */}
              <div>
                <label className={labelClass}>
                  Production guardrails
                </label>

                <button
                  onClick={() =>
                    setGuardrails(v => !v)
                  }
                  className="flex items-center gap-2"
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: saving
                      ? 'not-allowed'
                      : 'pointer',
                    padding: 0,
                    marginTop: 2,
                    opacity: saving ? 0.6 : 1,
                  }}
                  disabled={saving}
                >
                  <div
                    className="w-10 h-5 rounded-full flex items-center transition-all"
                    style={{
                      background: guardrails
                        ? '#1a1a1a'
                        : 'rgba(0,0,0,0.12)',
                      padding: '2px',
                      justifyContent: guardrails
                        ? 'flex-end'
                        : 'flex-start',
                    }}
                  >
                    <div
                      className="w-4 h-4 rounded-full bg-white"
                      style={{
                        boxShadow:
                          '0 1px 3px rgba(0,0,0,0.2)',
                      }}
                    />
                  </div>

                  <span
                    className="text-[13px] text-[#555]"
                    style={{
                      fontFamily:
                        'Questrial, sans-serif',
                    }}
                  >
                    {guardrails
                      ? 'Enabled'
                      : 'Disabled'}
                  </span>
                </button>
              </div>
            </div>

            {/* Fallback configuration */}
            <div
              className="mt-5 pt-5"
              style={{
                borderTop:
                  '1px solid rgba(0,0,0,0.07)',
              }}
            >
              <div className="grid grid-cols-2 gap-4">
                {/* Fallback provider */}
                <div>
                  <label className={labelClass}>
                    Fallback provider
                  </label>

                  <select
                    value={
                      settings.fallback_provider
                    }
                    onChange={e => {
                      const provider =
                        e.target.value as AIProvider

                      if (
                        provider ===
                        settings.provider
                      ) {
                        setError(
                          'Fallback provider must be different from the primary provider.',
                        )
                        return
                      }

                      updateSetting(
                        'fallback_provider',
                        provider,
                      )
                    }}
                    style={{
                      ...INPUT_STYLE,
                      opacity:
                        settings.fallback_enabled
                          ? 1
                          : 0.5,
                    }}
                    disabled={
                      !settings.fallback_enabled ||
                      saving
                    }
                  >
                    <option value="groq">
                      Groq
                    </option>

                    <option value="gemini">
                      Gemini
                    </option>

                    <option value="deterministic">
                      Deterministic
                    </option>
                  </select>
                </div>

                {/* Fallback toggle */}
                <div>
                  <label className={labelClass}>
                    LLM fallback
                  </label>

                  <button
                    onClick={() =>
                      updateSetting(
                        'fallback_enabled',
                        !settings.fallback_enabled,
                      )
                    }
                    className="flex items-center gap-2"
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: saving
                        ? 'not-allowed'
                        : 'pointer',
                      padding: 0,
                      marginTop: 2,
                      opacity: saving ? 0.6 : 1,
                    }}
                    disabled={saving}
                  >
                    <div
                      className="w-10 h-5 rounded-full flex items-center transition-all"
                      style={{
                        background:
                          settings.fallback_enabled
                            ? '#1a1a1a'
                            : 'rgba(0,0,0,0.12)',
                        padding: '2px',
                        justifyContent:
                          settings.fallback_enabled
                            ? 'flex-end'
                            : 'flex-start',
                      }}
                    >
                      <div className="w-4 h-4 rounded-full bg-white" />
                    </div>

                    <span
                      className="text-[13px] text-[#555]"
                      style={{
                        fontFamily:
                          'Questrial, sans-serif',
                      }}
                    >
                      {settings.fallback_enabled
                        ? 'Enabled'
                        : 'Disabled'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Application */}
          <div style={{ ...CARD, padding: '24px' }}>
            <div className={sectionTitle}>
              Application
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>
                  Application name
                </label>

                <input
                  value={appName}
                  onChange={e =>
                    setAppName(e.target.value)
                  }
                  style={{ ...INPUT_STYLE }}
                  disabled={saving}
                />
              </div>

              <div>
                <label className={labelClass}>
                  Log level
                </label>

                <select
                  value={logLevel}
                  onChange={e =>
                    setLogLevel(e.target.value)
                  }
                  style={{
                    ...INPUT_STYLE,
                    fontFamily:
                      'JetBrains Mono, monospace',
                    fontSize: 12,
                  }}
                  disabled={saving}
                >
                  <option value="debug">
                    debug
                  </option>
                  <option value="info">
                    info
                  </option>
                  <option value="warn">
                    warn
                  </option>
                  <option value="error">
                    error
                  </option>
                </select>
              </div>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div
              className="rounded-lg px-4 py-3 text-[13px]"
              style={{
                color: '#b91c1c',
                background:
                  'rgba(239,68,68,0.06)',
                border:
                  '1px solid rgba(239,68,68,0.18)',
              }}
            >
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between">
            <button
              style={{
                ...BTN_SECONDARY,
                color: '#b91c1c',
                borderColor:
                  'rgba(239,68,68,0.2)',
                background:
                  'rgba(239,68,68,0.06)',
                opacity: saving ? 0.6 : 1,
              }}
              onClick={reset}
              disabled={saving}
            >
              Reset to defaults
            </button>

            <button
              style={{
                ...BTN_PRIMARY,
                background: saved
                  ? '#22c55e'
                  : '#1a1a1a',
                minWidth: 120,
                justifyContent: 'center',
                opacity: saving ? 0.7 : 1,
              }}
              onClick={save}
              disabled={saving}
            >
              {saving ? (
                'Saving...'
              ) : saved ? (
                <>
                  <svg
                    width={14}
                    height={14}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2.5}
                    strokeLinecap="round"
                  >
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                  Saved
                </>
              ) : (
                'Save settings'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}