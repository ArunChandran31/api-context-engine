import { useEffect, useMemo, useState } from 'react'
import { getEndpoints, type ApiEndpoint } from '../api/endpoints'
import {
  getSpecifications,
  type ApiSpecification,
} from '../api/specifications'
import type { Page } from '../utils'
import { CARD, INPUT_STYLE, MethodBadge, methodColors } from '../utils'

interface Props {
  navigate: (p: Page, data?: unknown) => void
  data?: unknown
}

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

const METHODS: (Method | 'ALL')[] = [
  'ALL',
  'GET',
  'POST',
  'PUT',
  'PATCH',
  'DELETE',
]

function normalizeMethod(method: string): Method {
  const normalized = method.toUpperCase()

  if (
    normalized === 'GET' ||
    normalized === 'POST' ||
    normalized === 'PUT' ||
    normalized === 'PATCH' ||
    normalized === 'DELETE'
  ) {
    return normalized
  }

  return 'GET'
}

function getEndpointTag(path: string): string {
  const segments = path.split('/').filter(Boolean)

  if (segments.length === 0) {
    return 'General'
  }

  return segments[0]
}

function toEndpointViewModel(endpoint: ApiEndpoint) {
  return {
    ...endpoint,
    method: normalizeMethod(endpoint.method),
    summary: endpoint.summary ?? 'No description available',
    tag: getEndpointTag(endpoint.path),
  }
}

export default function APIExplorer({ navigate, data }: Props) {
  const navigationData =
    data &&
    typeof data === 'object' &&
    !Array.isArray(data)
      ? data as { specificationId?: number }
      : undefined

  const requestedSpecificationId =
    typeof navigationData?.specificationId === 'number'
      ? navigationData.specificationId
      : null
  const [specifications, setSpecifications] = useState<ApiSpecification[]>([])
  const [selectedSpecificationId, setSelectedSpecificationId] = useState<
    number | null
  >(null)
  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>([])

  const [search, setSearch] = useState('')
  const [method, setMethod] = useState<Method | 'ALL'>('ALL')

  const [loadingSpecifications, setLoadingSpecifications] = useState(true)
  const [loadingEndpoints, setLoadingEndpoints] = useState(false)

  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadSpecifications() {
      try {
        setLoadingSpecifications(true)
        setError(null)

        const data = await getSpecifications()

        if (cancelled) {
          return
        }

        setSpecifications(data)

        if (data.length > 0) {
          const requestedSpecificationExists =
            requestedSpecificationId !== null &&
            data.some(
              (specification) =>
                specification.id === requestedSpecificationId,
            )

          setSelectedSpecificationId(
            requestedSpecificationExists
              ? requestedSpecificationId
              : data[0].id,
          )
        }
      } catch (err) {
        if (cancelled) {
          return
        }

        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load API specifications.',
        )
      } finally {
        if (!cancelled) {
          setLoadingSpecifications(false)
        }
      }
    }

    loadSpecifications()

    return () => {
      cancelled = true
    }
  }, [requestedSpecificationId])

  useEffect(() => {
    if (selectedSpecificationId === null) {
      setEndpoints([])
      return
    }

    let cancelled = false

    async function loadEndpoints() {
      const specificationId = selectedSpecificationId

      if (specificationId === null) {
        return
      }

      try {
        setLoadingEndpoints(true)
        setError(null)

        const data = await getEndpoints(specificationId)

        if (cancelled) {
          return
        }

        setEndpoints(data)
      } catch (err) {
        if (cancelled) {
          return
        }

        setEndpoints([])
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load endpoints.',
        )
      } finally {
        if (!cancelled) {
          setLoadingEndpoints(false)
        }
      }
    }

    loadEndpoints()

    return () => {
      cancelled = true
    }
  }, [selectedSpecificationId])

  const selectedSpecification = specifications.find(
    (specification) => specification.id === selectedSpecificationId,
  )

  const filtered = useMemo(() => {
    const query = search.toLowerCase()

    return endpoints
      .map(toEndpointViewModel)
      .filter((endpoint) => {
        const matchMethod =
          method === 'ALL' || endpoint.method === method

        const matchSearch =
          endpoint.path.toLowerCase().includes(query) ||
          endpoint.summary.toLowerCase().includes(query) ||
          endpoint.tag.toLowerCase().includes(query)

        return matchMethod && matchSearch
      })
  }, [endpoints, method, search])

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-[26px] font-semibold text-[#1a1a1a]">
          API Explorer
        </h1>
        <p className="text-[14px] text-[#888] mt-0.5">
          Browse endpoints and schemas across your specifications
        </p>
      </div>

      {/* Controls */}
      <div
        style={{
          ...CARD,
          padding: '16px 18px',
          marginBottom: 16,
        }}
      >
        <div className="flex items-center gap-3 flex-wrap">
          {/* Spec selector */}
          <select
            value={selectedSpecificationId ?? ''}
            onChange={(event) => {
              const value = event.target.value

              setSelectedSpecificationId(
                value ? Number(value) : null,
              )

              setMethod('ALL')
              setSearch('')
            }}
            disabled={
              loadingSpecifications || specifications.length === 0
            }
            style={{
              ...INPUT_STYLE,
              width: 'auto',
              borderRadius: '12px',
              paddingRight: 32,
            }}
          >
            {loadingSpecifications && (
              <option value="">Loading specifications...</option>
            )}

            {!loadingSpecifications &&
              specifications.length === 0 && (
                <option value="">No specifications found</option>
              )}

            {specifications.map((specification) => (
              <option
                key={specification.id}
                value={specification.id}
              >
                {specification.title}
              </option>
            ))}
          </select>

          {/* Search */}
          <div
            className="flex-1 relative"
            style={{ minWidth: 200 }}
          >
            <svg
              width={14}
              height={14}
              viewBox="0 0 24 24"
              fill="none"
              stroke="#aaa"
              strokeWidth={2}
              strokeLinecap="round"
              className="absolute left-3 top-1/2 -translate-y-1/2"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>

            <input
              style={{
                ...INPUT_STYLE,
                paddingLeft: 34,
              }}
              placeholder="Search by path, tag or description..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          {/* Method filter */}
          <div className="flex gap-1">
            {METHODS.map((currentMethod) => {
              const active = method === currentMethod

              const color =
                currentMethod !== 'ALL'
                  ? methodColors(currentMethod)
                  : null

              return (
                <button
                  key={currentMethod}
                  onClick={() => setMethod(currentMethod)}
                  className="px-3 py-1.5 rounded-full text-[12px] font-medium transition-all"
                  style={{
                    background: active
                      ? color
                        ? color.bg
                        : '#1a1a1a'
                      : 'transparent',
                    color: active
                      ? color
                        ? color.text
                        : '#fff'
                      : '#888',
                    border: active
                      ? `1px solid ${
                          color ? color.border : '#1a1a1a'
                        }`
                      : '1px solid rgba(0,0,0,0.08)',
                    fontFamily: 'JetBrains Mono, monospace',
                    cursor: 'pointer',
                  }}
                >
                  {currentMethod}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div
          className="mb-4 px-4 py-3 rounded-[16px] text-[13px]"
          style={{
            background: 'rgba(220, 38, 38, 0.06)',
            border: '1px solid rgba(220, 38, 38, 0.15)',
            color: '#b42318',
          }}
        >
          {error}
        </div>
      )}

      {/* Endpoint list */}
      <div
        style={{
          ...CARD,
          padding: 0,
          overflow: 'hidden',
        }}
      >
        <div
          className="px-5 py-3 flex items-center justify-between"
          style={{
            borderBottom:
              '1px solid rgba(0,0,0,0.06)',
          }}
        >
          <span className="text-[13px] text-[#888]">
            {loadingEndpoints
              ? 'Loading endpoints...'
              : `${filtered.length} endpoints`}
          </span>

          <span className="text-[12px] font-mono text-[#aaa]">
            {selectedSpecification?.title ?? 'No specification selected'}
          </span>
        </div>

        {loadingEndpoints && (
          <div className="flex flex-col items-center py-16 text-[#aaa]">
            <div className="text-[14px]">
              Loading endpoints...
            </div>
          </div>
        )}

        {!loadingEndpoints &&
          filtered.length === 0 && (
            <div className="flex flex-col items-center py-16 text-[#aaa]">
              <svg
                width={32}
                height={32}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
                strokeLinecap="round"
                className="mb-3"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>

              <div className="text-[14px]">
                {endpoints.length === 0
                  ? 'No endpoints available for this specification'
                  : 'No endpoints match your filters'}
              </div>
            </div>
          )}

        {!loadingEndpoints &&
          filtered.map((endpoint, index) => (
            <div
              key={endpoint.id}
              className="flex items-center gap-4 px-5 py-3.5 cursor-pointer hover:bg-black/[0.02] transition-colors"
              style={
                index < filtered.length - 1
                  ? {
                      borderBottom:
                        '1px solid rgba(0,0,0,0.04)',
                    }
                  : {}
              }
              onClick={() =>
                navigate('endpoint', endpoint)
              }
            >
              <MethodBadge method={endpoint.method} />

              <span className="font-mono text-[13px] text-[#1a1a1a] flex-1">
                {endpoint.path}
              </span>

              <span className="text-[13px] text-[#888] flex-1">
                {endpoint.summary}
              </span>

              <span
                className="px-2 py-0.5 rounded-full text-[11px] text-[#888]"
                style={{
                  background: 'rgba(0,0,0,0.05)',
                }}
              >
                {endpoint.tag}
              </span>

              <button
                className="text-[13px] px-3 py-1 rounded-[10px] text-[#555]"
                style={{
                  background: 'rgba(0,0,0,0.06)',
                  border: 'none',
                  cursor: 'pointer',
                  fontFamily: 'Questrial, sans-serif',
                }}
                onClick={(event) => {
                  event.stopPropagation()
                  navigate('endpoint', endpoint)
                }}
              >
                Open
              </button>
            </div>
          ))}
      </div>
    </div>
  )
}