import { useEffect, useState } from 'react'
import type { Page } from '../utils'
import { CARD, BTN_PRIMARY, BTN_SECONDARY } from '../utils'
import {
  getSpecifications,
  type ApiSpecification,
} from '../api/specifications'
import {
  getEndpoints,
  type ApiEndpoint,
} from '../api/endpoints'

interface Props {
  navigate: (p: Page) => void
}

function StatCard({
  label,
  value,
  sub,
}: {
  label: string
  value: string | number
  sub?: string
}) {
  return (
    <div style={{ ...CARD, padding: '20px 24px' }}>
      <div className="text-[13px] text-[#888] mb-1">
        {label}
      </div>

      <div className="text-[32px] font-semibold text-[#1a1a1a] leading-none">
        {value}
      </div>

      {sub && (
        <div className="text-[12px] text-[#aaa] mt-1">
          {sub}
        </div>
      )}
    </div>
  )
}

function StatusBadge({
  status,
}: {
  status: 'Healthy' | 'Degraded' | 'Error'
}) {
  const colors = {
    Healthy: {
      bg: '#dcfce7',
      text: '#15803d',
      dot: '#22c55e',
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

  const c = colors[status]

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

function formatUpdatedAt(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown'
  }

  const diffMs = Date.now() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)

  if (diffMinutes < 1) {
    return 'Just now'
  }

  if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`
  }

  const diffHours = Math.floor(diffMinutes / 60)

  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`
  }

  const diffDays = Math.floor(diffHours / 24)

  if (diffDays < 7) {
    return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`
  }

  return date.toLocaleDateString()
}

export default function Dashboard({ navigate }: Props) {
  const [specifications, setSpecifications] = useState<
    ApiSpecification[]
  >([])

  const [endpointCounts, setEndpointCounts] = useState<
    Record<number, number>
  >({})

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true)
        setError(null)

        const specs = await getSpecifications()

        setSpecifications(specs)

        const counts: Record<number, number> = {}

        await Promise.all(
          specs.map(async (specification) => {
            try {
              const endpoints = await getEndpoints(
                specification.id,
              )

              counts[specification.id] = endpoints.length
            } catch (endpointError) {
              console.error(
                `Failed to load endpoints for specification ${specification.id}:`,
                endpointError,
              )

              counts[specification.id] = 0
            }
          }),
        )

        setEndpointCounts(counts)
      } catch (loadError) {
        console.error(
          'Failed to load dashboard:',
          loadError,
        )

        setError(
          loadError instanceof Error
            ? loadError.message
            : 'Failed to load dashboard data.',
        )
      } finally {
        setLoading(false)
      }
    }

    loadDashboard()
  }, [])

  const totalEndpoints = Object.values(endpointCounts).reduce(
    (total, count) => total + count,
    0,
  )

  /*
   * Specifications are returned in creation order by the
   * current backend, so reverse them to show the newest first.
   */
  const recentSpecifications = [...specifications]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() -
        new Date(a.created_at).getTime(),
    )
    .slice(0, 5)

  return (
    <div>
      {/* Page header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-[26px] font-semibold text-[#1a1a1a]">
            Dashboard
          </h1>

          <p className="text-[14px] text-[#888] mt-0.5">
            Your developer workspace
          </p>
        </div>

        <div className="flex items-center gap-2 mt-1">
          <button
            style={BTN_SECONDARY}
            onClick={() => navigate('assistant')}
          >
            <svg
              width={14}
              height={14}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
            >
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>

            New Question
          </button>

          <button
            style={BTN_PRIMARY}
            onClick={() => navigate('upload')}
          >
            <svg
              width={14}
              height={14}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
            >
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
            </svg>

            Upload API
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div
          className="mb-5 rounded-[14px] px-4 py-3 text-[13px]"
          style={{
            background: '#fee2e2',
            color: '#b91c1c',
            border: '1px solid rgba(185,28,28,0.12)',
          }}
        >
          Failed to load dashboard data: {error}
        </div>
      )}

      {/* Overview label */}
      <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">
        Overview
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <StatCard
          label="API Specifications"
          value={loading ? '—' : specifications.length}
          sub="indexed"
        />

        <StatCard
          label="Endpoints"
          value={loading ? '—' : totalEndpoints}
          sub="across all specs"
        />

        <StatCard
          label="AI Queries"
          value="—"
          sub="session tracking coming soon"
        />

        <div
          style={{
            ...CARD,
            padding: '20px 24px',
          }}
        >
          <div className="text-[13px] text-[#888] mb-1">
            System Status
          </div>

          <div className="mt-1">
            <StatusBadge
              status={error ? 'Degraded' : 'Healthy'}
            />
          </div>

          <div className="text-[12px] text-[#aaa] mt-2">
            {error
              ? 'Some services may be unavailable'
              : 'All services operational'}
          </div>
        </div>
      </div>

      {/* Recent API specifications */}
      <div className="mb-6">
        <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">
          Recent API specifications
        </div>

        <div
          style={{
            ...CARD,
            padding: 0,
            overflow: 'hidden',
          }}
        >
          {loading ? (
            <div className="px-5 py-8 text-center text-[13px] text-[#aaa]">
              Loading API specifications...
            </div>
          ) : recentSpecifications.length === 0 ? (
            <div className="px-5 py-8 text-center">
              <div className="text-[14px] text-[#555]">
                No API specifications found.
              </div>

              <div className="text-[12px] text-[#aaa] mt-1">
                Upload an OpenAPI specification to get started.
              </div>

              <button
                style={{
                  ...BTN_PRIMARY,
                  marginTop: 14,
                }}
                onClick={() => navigate('upload')}
              >
                Upload API
              </button>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr
                  style={{
                    borderBottom:
                      '1px solid rgba(0,0,0,0.06)',
                  }}
                >
                  <th className="text-left px-5 py-3 text-[12px] text-[#aaa] font-medium">
                    Name
                  </th>

                  <th className="text-left px-5 py-3 text-[12px] text-[#aaa] font-medium">
                    Endpoints
                  </th>

                  <th className="text-left px-5 py-3 text-[12px] text-[#aaa] font-medium">
                    Last updated
                  </th>

                  <th className="text-left px-5 py-3 text-[12px] text-[#aaa] font-medium">
                    Status
                  </th>

                  <th className="px-5 py-3" />
                </tr>
              </thead>

              <tbody>
                {recentSpecifications.map(
                  (specification, index) => {
                    const endpointCount =
                      endpointCounts[specification.id] ?? 0

                    return (
                      <tr
                        key={specification.id}
                        className="hover:bg-black/[0.02] transition-colors"
                        style={
                          index <
                          recentSpecifications.length - 1
                            ? {
                                borderBottom:
                                  '1px solid rgba(0,0,0,0.05)',
                              }
                            : {}
                        }
                      >
                        <td className="px-5 py-3.5">
                          <div className="text-[14px] font-medium text-[#1a1a1a]">
                            {specification.title}
                          </div>

                          {specification.version && (
                            <div className="text-[11px] text-[#aaa] mt-0.5">
                              v{specification.version}
                            </div>
                          )}
                        </td>

                        <td className="px-5 py-3.5 text-[13px] text-[#666] font-mono">
                          {endpointCount}
                        </td>

                        <td className="px-5 py-3.5 text-[13px] text-[#888]">
                          {formatUpdatedAt(
                            specification.created_at,
                          )}
                        </td>

                        <td className="px-5 py-3.5">
                          <StatusBadge status="Healthy" />
                        </td>

                        <td className="px-5 py-3.5 text-right">
                          <button
                            onClick={() =>
                              navigate('explorer')
                            }
                            className="text-[13px] text-[#1a1a1a] hover:text-black"
                            style={{
                              background:
                                'rgba(0,0,0,0.06)',
                              border: 'none',
                              borderRadius: '12px',
                              padding: '5px 14px',
                              cursor: 'pointer',
                              fontFamily:
                                'Questrial, sans-serif',
                            }}
                          >
                            Open
                          </button>
                        </td>
                      </tr>
                    )
                  },
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div>
        <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">
          Quick actions
        </div>

        <div className="grid grid-cols-3 gap-3">
          {[
            {
              label: 'Explore APIs',
              desc: 'Browse endpoints and schemas',
              page: 'explorer' as Page,
              icon: 'M12 2L2 7l10 5 10-5-10-5M2 17l10 5 10-5M2 12l10 5 10-5',
            },
            {
              label: 'Ask AI',
              desc: 'Query your API context with AI',
              page: 'assistant' as Page,
              icon: 'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z',
            },
            {
              label: 'Generate tests',
              desc: 'Auto-generate test cases',
              page: 'tests' as Page,
              icon: 'M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11',
            },
          ].map((action) => (
            <button
              key={action.label}
              onClick={() => navigate(action.page)}
              className="text-left"
              style={{
                ...CARD,
                padding: '20px 22px',
                cursor: 'pointer',
                border: '1px solid transparent',
                transition: 'all 150ms',
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.border =
                  '1px solid rgba(0,0,0,0.1)')
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.border =
                  '1px solid transparent')
              }
            >
              <div
                className="mb-3 w-8 h-8 rounded-[10px] flex items-center justify-center"
                style={{
                  background: 'rgba(0,0,0,0.06)',
                }}
              >
                <svg
                  width={16}
                  height={16}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#1a1a1a"
                  strokeWidth={2}
                  strokeLinecap="round"
                >
                  <path d={action.icon} />
                </svg>
              </div>

              <div className="text-[14px] font-semibold text-[#1a1a1a]">
                {action.label}
              </div>

              <div className="text-[12px] text-[#888] mt-0.5">
                {action.desc}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}