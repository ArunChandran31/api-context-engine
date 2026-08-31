import { useEffect, useState } from 'react'
import type { Page } from '../utils'
import { CARD } from '../utils'
import {
  getHealth,
  type HealthResponse,
  type HealthService,
} from '../api/health'

interface Props {
  navigate: (p: Page) => void
}

type DisplayStatus = 'Healthy' | 'Configured' | 'Degraded' | 'Error'

const STATUS_COLORS: Record<
  DisplayStatus,
  { bg: string; text: string; dot: string }
> = {
  Healthy: {
    bg: '#dcfce7',
    text: '#15803d',
    dot: '#22c55e',
  },
  Configured: {
    bg: '#dbeafe',
    text: '#1d4ed8',
    dot: '#3b82f6',
  },
  Degraded: {
    bg: '#fef3c7',
    text: '#b45309',
    dot: '#f59e0b',
  },
  Error: {
    bg: '#fee2e2',
    text: '#b91c1c',
    dot: '#ef4444',
  },
}

function toDisplayStatus(status: HealthService['status']): DisplayStatus {
  switch (status) {
    case 'healthy':
      return 'Healthy'
    case 'configured':
      return 'Configured'
    case 'degraded':
      return 'Degraded'
    case 'error':
      return 'Error'
  }
}

function StatusPill({ status }: { status: DisplayStatus }) {
  const c = STATUS_COLORS[status]

  return (
    <span
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-medium"
      style={{
        background: c.bg,
        color: c.text,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ background: c.dot }}
      />
      {status}
    </span>
  )
}

function serviceDetail(
  name: keyof HealthResponse['services'],
  service: HealthService,
): string {
  if (service.message) {
    return service.message
  }

  if (name === 'database') {
    return 'Database connection is responding normally'
  }

  if (name === 'redis') {
    return 'Redis connection is responding normally'
  }

  if (name === 'vector_store') {
    const type = service.type ?? 'Unknown vector store'
    const records =
      typeof service.records === 'number'
        ? `${service.records} records`
        : 'record count unavailable'
    const dimension =
      typeof service.dimension === 'number'
        ? ` · ${service.dimension} dimensions`
        : ''

    return `${type} · ${records}${dimension}`
  }

  if (name === 'llm') {
    const provider = service.provider ?? 'Unknown provider'
    const model = service.model ?? 'Unknown model'

    return `${provider} · ${model}`
  }

  return 'Status available'
}

const SERVICE_LABELS: Array<{
  key: keyof HealthResponse['services']
  label: string
}> = [
  {
    key: 'database',
    label: 'Database',
  },
  {
    key: 'redis',
    label: 'Redis cache',
  },
  {
    key: 'vector_store',
    label: 'Vector store',
  },
  {
    key: 'llm',
    label: 'LLM provider',
  },
]

const PIPELINE_STAGES = [
  {
    id: 'ingest',
    label: 'Ingest',
  },
  {
    id: 'chunk',
    label: 'Chunk',
  },
  {
    id: 'embed',
    label: 'Embed',
  },
  {
    id: 'index',
    label: 'Index',
  },
  {
    id: 'retrieve',
    label: 'Retrieve',
  },
]

export default function SystemStatus({ navigate: _navigate }: Props) {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    async function loadHealth() {
      try {
        setLoading(true)
        setError(null)

        const response = await getHealth()

        if (mounted) {
          setHealth(response)
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Failed to load system health.',
          )
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    loadHealth()

    return () => {
      mounted = false
    }
  }, [])

  const overallStatus: DisplayStatus =
    health?.status === 'healthy' ? 'Healthy' : 'Degraded'

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-[26px] font-semibold text-[#1a1a1a]">
            System Status
          </h1>

          <p className="text-[14px] text-[#888] mt-0.5">
            Live service health and infrastructure overview
          </p>
        </div>

        {!loading && (
          <div className="flex items-center gap-2 mt-1">
            <StatusPill
              status={error ? 'Error' : overallStatus}
            />
          </div>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div
          style={{
            ...CARD,
            padding: '24px',
          }}
          className="text-[14px] text-[#888]"
        >
          Checking system health...
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div
          className="rounded-[14px] p-4 mb-4 text-[13px]"
          style={{
            background: '#fee2e2',
            color: '#b91c1c',
            border: '1px solid rgba(185,28,28,0.12)',
          }}
        >
          Failed to load system health: {error}
        </div>
      )}

      {/* Services */}
      {!loading && health && (
        <>
          <div className="mb-4">
            <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">
              Services
            </div>

            <div
              style={{
                ...CARD,
                padding: 0,
                overflow: 'hidden',
              }}
            >
              {SERVICE_LABELS.map((service, index) => {
                const healthService =
                  health.services[service.key]

                const status = toDisplayStatus(
                  healthService.status,
                )

                return (
                  <div
                    key={service.key}
                    className="flex items-center justify-between px-5 py-4"
                    style={
                      index < SERVICE_LABELS.length - 1
                        ? {
                            borderBottom:
                              '1px solid rgba(0,0,0,0.05)',
                          }
                        : {}
                    }
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-8 h-8 rounded-[10px] flex items-center justify-center"
                        style={{
                          background:
                            STATUS_COLORS[status].bg,
                        }}
                      >
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{
                            background:
                              STATUS_COLORS[status].dot,
                          }}
                        />
                      </div>

                      <div>
                        <div className="text-[14px] font-medium text-[#1a1a1a]">
                          {service.label}
                        </div>

                        <div className="text-[12px] text-[#aaa] mt-0.5">
                          {serviceDetail(
                            service.key,
                            healthService,
                          )}
                        </div>
                      </div>
                    </div>

                    <StatusPill status={status} />
                  </div>
                )
              })}
            </div>
          </div>

          {/* RAG Pipeline */}
          <div>
            <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">
              RAG pipeline
            </div>

            <div
              style={{
                ...CARD,
                padding: '24px',
              }}
            >
              <div className="flex items-center gap-0">
                {PIPELINE_STAGES.map((stage, index) => {
                  const stageStatus: DisplayStatus =
                    health.services.vector_store.status ===
                      'error' ||
                    health.services.vector_store.status ===
                      'degraded'
                      ? 'Degraded'
                      : 'Healthy'

                  const c = STATUS_COLORS[stageStatus]

                  return (
                    <div
                      key={stage.id}
                      className="flex items-center flex-1"
                    >
                      <div className="flex flex-col items-center flex-1">
                        <div
                          className="w-10 h-10 rounded-full flex items-center justify-center mb-2"
                          style={{
                            background: c.bg,
                            border: `2px solid ${c.dot}`,
                          }}
                        >
                          <div
                            className="w-2.5 h-2.5 rounded-full"
                            style={{
                              background: c.dot,
                            }}
                          />
                        </div>

                        <div className="text-[13px] font-medium text-[#1a1a1a] text-center">
                          {stage.label}
                        </div>

                        <StatusPill status={stageStatus} />
                      </div>

                      {index <
                        PIPELINE_STAGES.length - 1 && (
                        <div className="flex items-center flex-shrink-0 px-1 pb-7">
                          <div
                            className="h-px w-6"
                            style={{
                              background:
                                'rgba(0,0,0,0.12)',
                            }}
                          />

                          <svg
                            width={8}
                            height={12}
                            viewBox="0 0 8 12"
                            fill="none"
                            className="flex-shrink-0"
                          >
                            <path
                              d="M1 1l6 5-6 5"
                              stroke="rgba(0,0,0,0.2)"
                              strokeWidth={1.5}
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              <div
                className="mt-5 rounded-[14px] p-4 text-[13px] text-[#555] leading-relaxed"
                style={{
                  background: 'rgba(0,0,0,0.03)',
                  border:
                    '1px solid rgba(0,0,0,0.05)',
                }}
              >
                <span className="font-medium text-[#1a1a1a]">
                  Pipeline summary:
                </span>{' '}
                Specifications are ingested from file or URL,
                chunked by endpoint and schema, embedded using
                the configured embedding model, indexed in the
                FAISS vector store, and retrieved via semantic
                search during AI queries.
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
