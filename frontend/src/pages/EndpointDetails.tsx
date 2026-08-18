import { useState } from 'react'
import type { ApiEndpoint } from '../api/endpoints'
import type { Page } from '../utils'
import { CARD, MethodBadge } from '../utils'

interface Props {
  navigate: (p: Page, data?: unknown) => void
  data?: unknown
}

interface Section {
  id: string
  label: string
  content: React.ReactNode
}

function Accordion({ sections }: { sections: Section[] }) {
  const [open, setOpen] = useState<string | null>(
    sections[0]?.id ?? null,
  )

  return (
    <div style={{ ...CARD, padding: 0, overflow: 'hidden' }}>
      {sections.map((section, index) => (
        <div
          key={section.id}
          style={
            index < sections.length - 1
              ? { borderBottom: '1px solid rgba(0,0,0,0.06)' }
              : {}
          }
        >
          <button
            onClick={() =>
              setOpen(open === section.id ? null : section.id)
            }
            className="w-full flex items-center justify-between px-5 py-3.5 text-left"
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'Questrial, sans-serif',
            }}
          >
            <span className="text-[14px] font-medium text-[#1a1a1a]">
              {section.label}
            </span>

            <svg
              width={14}
              height={14}
              viewBox="0 0 24 24"
              fill="none"
              stroke="#aaa"
              strokeWidth={2}
              strokeLinecap="round"
              style={{
                transform:
                  open === section.id
                    ? 'rotate(180deg)'
                    : 'rotate(0deg)',
                transition: 'transform 200ms',
              }}
            >
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>

          {open === section.id && (
            <div className="px-5 pb-4 text-[13px] text-[#555]">
              {section.content}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function Code({ children }: { children: string }) {
  return (
    <pre
      className="rounded-[12px] p-4 text-[12px] overflow-x-auto"
      style={{
        background: '#f5f5f5',
        border: '1px solid rgba(0,0,0,0.06)',
        fontFamily: 'JetBrains Mono, monospace',
        lineHeight: 1.6,
      }}
    >
      {children}
    </pre>
  )
}

function getSchemaType(
  schema: Record<string, unknown> | undefined,
): string {
  if (!schema) {
    return 'unknown'
  }

  if (typeof schema.type === 'string') {
    return schema.type
  }

  if (Array.isArray(schema.enum)) {
    return 'enum'
  }

  return 'object'
}

function getSchemaDetails(
  schema: Record<string, unknown> | undefined,
): {
  format?: string
  enumValues?: string[]
  defaultValue?: unknown
  nullable?: boolean
} {
  if (!schema) {
    return {}
  }

  const details: {
    format?: string
    enumValues?: string[]
    defaultValue?: unknown
    nullable?: boolean
  } = {}

  if (typeof schema.format === 'string') {
    details.format = schema.format
  }

  if (Array.isArray(schema.enum)) {
    details.enumValues = schema.enum.map(String)
  }

  if ('default' in schema) {
    details.defaultValue = schema.default
  }

  if (typeof schema.nullable === 'boolean') {
    details.nullable = schema.nullable
  }

  return details
}

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

function getResponseStyle(code: string) {
  const numericCode = Number(code)

  if (numericCode >= 200 && numericCode < 300) {
    return {
      background: '#dcfce7',
      color: '#15803d',
    }
  }

  if (numericCode >= 400 && numericCode < 500) {
    return {
      background: '#fef3c7',
      color: '#b45309',
    }
  }

  if (numericCode >= 500) {
    return {
      background: '#fee2e2',
      color: '#b91c1c',
    }
  }

  return {
    background: '#f3f4f6',
    color: '#555',
  }
}

function renderParameters(ep: ApiEndpoint) {
  const parameters = ep.parameters ?? []

  if (parameters.length === 0) {
    return (
      <div className="text-[13px] text-[#888]">
        No parameters defined for this endpoint.
      </div>
    )
  }

  return (
    <table className="w-full text-[13px]">
      <thead>
        <tr
          style={{
            borderBottom: '1px solid rgba(0,0,0,0.06)',
          }}
        >
          {['Name', 'In', 'Type', 'Required', 'Description'].map(
            (heading) => (
              <th
                key={heading}
                className="text-left pb-2 text-[12px] text-[#aaa] font-medium pr-4"
              >
                {heading}
              </th>
            ),
          )}
        </tr>
      </thead>

      <tbody>
        {parameters.map((parameter, index) => {
          const schema =
            parameter.schema &&
            typeof parameter.schema === 'object'
              ? parameter.schema
              : undefined

          const required = parameter.required === true
          const schemaDetails = getSchemaDetails(schema)

          return (
            <tr
              key={`${parameter.name}-${parameter.in}-${index}`}
              style={{
                borderBottom:
                  index < parameters.length - 1
                    ? '1px solid rgba(0,0,0,0.04)'
                    : undefined,
              }}
            >
              <td className="py-2 pr-4 font-mono text-[#1a1a1a]">
                {parameter.name}
              </td>

              <td className="py-2 pr-4 text-[#666]">
                {parameter.in}
              </td>

              <td className="py-2 pr-4 font-mono text-[#888]">
                {getSchemaType(schema)}
              </td>

              <td className="py-2 pr-4">
                <span
                  className="px-2 py-0.5 rounded-full text-[11px]"
                  style={{
                    background: required
                      ? '#dcfce7'
                      : 'rgba(0,0,0,0.05)',
                    color: required ? '#15803d' : '#888',
                  }}
                >
                  {required ? 'Yes' : 'No'}
                </span>
              </td>

              <td className="py-2 text-[#666]">
                <div>
                  {parameter.description ?? 'No description'}
                </div>

                {(schemaDetails.format ||
                  schemaDetails.enumValues ||
                  'defaultValue' in schemaDetails ||
                  schemaDetails.nullable !== undefined) && (
                  <div className="flex flex-wrap gap-2 mt-1.5">
                    {schemaDetails.format && (
                      <span
                        className="px-2 py-0.5 rounded-full text-[11px] font-mono"
                        style={{
                          background: 'rgba(0,0,0,0.05)',
                          color: '#666',
                        }}
                      >
                        format: {schemaDetails.format}
                      </span>
                    )}

                    {schemaDetails.enumValues && (
                      <span
                        className="px-2 py-0.5 rounded-full text-[11px] font-mono"
                        style={{
                          background: '#f3f4f6',
                          color: '#666',
                        }}
                      >
                        enum: {schemaDetails.enumValues.join(' | ')}
                      </span>
                    )}

                    {'defaultValue' in schemaDetails && (
                      <span
                        className="px-2 py-0.5 rounded-full text-[11px] font-mono"
                        style={{
                          background: '#f3f4f6',
                          color: '#666',
                        }}
                      >
                        default: {String(schemaDetails.defaultValue)}
                      </span>
                    )}

                    {schemaDetails.nullable !== undefined && (
                      <span
                        className="px-2 py-0.5 rounded-full text-[11px]"
                        style={{
                          background: schemaDetails.nullable
                            ? '#dbeafe'
                            : 'rgba(0,0,0,0.05)',
                          color: schemaDetails.nullable
                            ? '#1d4ed8'
                            : '#888',
                        }}
                      >
                        {schemaDetails.nullable
                          ? 'nullable'
                          : 'non-nullable'}
                      </span>
                    )}
                  </div>
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function renderRequestBody(ep: ApiEndpoint) {
  if (!ep.request_body) {
    return (
      <div className="text-[13px] text-[#888]">
        No request body defined for this endpoint.
      </div>
    )
  }

  const requestBody = ep.request_body
  const required = requestBody.required === true

  const content =
    requestBody.content &&
    typeof requestBody.content === 'object' &&
    !Array.isArray(requestBody.content)
      ? requestBody.content as Record<string, unknown>
      : {}

  const contentEntries = Object.entries(content)

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <span className="text-[13px] text-[#555]">
          Required
        </span>

        <span
          className="px-2 py-0.5 rounded-full text-[11px]"
          style={{
            background: required
              ? '#dcfce7'
              : 'rgba(0,0,0,0.05)',
            color: required ? '#15803d' : '#888',
          }}
        >
          {required ? 'Yes' : 'No'}
        </span>
      </div>

      {contentEntries.length === 0 ? (
        <div className="text-[13px] text-[#888]">
          No content schema defined.
        </div>
      ) : (
        contentEntries.map(([contentType, mediaType]) => (
          <div key={contentType} className="flex flex-col gap-2">
            <div className="text-[12px] text-[#aaa] font-medium">
              Content type
            </div>

            <div className="font-mono text-[13px] text-[#1a1a1a]">
              {contentType}
            </div>

            <Code>
              {formatJson(mediaType)}
            </Code>
          </div>
        ))
      )}
    </div>
  )
}

function renderResponses(ep: ApiEndpoint) {
  const responses = ep.responses ?? {}
  const entries = Object.entries(responses)

  if (entries.length === 0) {
    return (
      <div className="text-[13px] text-[#888]">
        No responses defined for this endpoint.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {entries.map(([code, response]) => {
        const style = getResponseStyle(code)

        const description =
          response &&
          typeof response.description === 'string'
            ? response.description
            : 'No description'

        const content =
          response &&
          typeof response.content === 'object' &&
          !Array.isArray(response.content)
            ? response.content as Record<string, unknown>
            : {}

        const contentEntries = Object.entries(content)

        return (
          <div
            key={code}
            className="flex flex-col gap-3"
          >
            <div className="flex items-start gap-3">
              <span
                className="font-mono text-[13px] px-2 py-0.5 rounded-full font-semibold"
                style={style}
              >
                {code}
              </span>

              <span className="text-[13px] text-[#555]">
                {description}
              </span>
            </div>

            {contentEntries.length > 0 && (
              <div className="ml-0 flex flex-col gap-3">
                {contentEntries.map(
                  ([contentType, mediaType]) => {
                    const mediaTypeObject =
                      mediaType &&
                      typeof mediaType === 'object' &&
                      !Array.isArray(mediaType)
                        ? mediaType as Record<string, unknown>
                        : {}

                    const schema =
                      mediaTypeObject.schema &&
                      typeof mediaTypeObject.schema === 'object' &&
                      !Array.isArray(mediaTypeObject.schema)
                        ? mediaTypeObject.schema as Record<
                            string,
                            unknown
                          >
                        : undefined

                    return (
                      <div
                        key={contentType}
                        className="rounded-[12px] p-3"
                        style={{
                          background:
                            'rgba(0,0,0,0.025)',
                          border:
                            '1px solid rgba(0,0,0,0.05)',
                        }}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-[12px] text-[#aaa]">
                            Content type
                          </span>

                          <span className="font-mono text-[12px] text-[#1a1a1a]">
                            {contentType}
                          </span>
                        </div>

                        {schema ? (
                          <div className="flex flex-col gap-2">
                            <div className="text-[12px] text-[#aaa]">
                              Schema
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[13px] text-[#1a1a1a]">
                                {getSchemaType(schema)}
                              </span>

                              {typeof schema.format === 'string' && (
                                <span
                                  className="px-2 py-0.5 rounded-full text-[11px] font-mono"
                                  style={{
                                    background:
                                      'rgba(0,0,0,0.05)',
                                    color: '#666',
                                  }}
                                >
                                  {schema.format}
                                </span>
                              )}
                            </div>

                            <Code>
                              {formatJson(schema)}
                            </Code>
                          </div>
                        ) : (
                          <div className="text-[13px] text-[#888]">
                            No response schema defined.
                          </div>
                        )}
                      </div>
                    )
                  },
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function renderSecurity(ep: ApiEndpoint) {
  const security = ep.security ?? []

  if (security.length === 0) {
    return (
      <div className="text-[13px] text-[#888]">
        No security requirements defined for this endpoint.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {security.map((requirement, index) => (
        <div
          key={index}
          className="flex flex-col gap-2"
        >
          {Object.entries(requirement).map(
            ([scheme, scopes]) => (
              <div
                key={scheme}
                className="flex items-center gap-2 flex-wrap"
              >
                <span className="font-mono text-[#1a1a1a]">
                  {scheme}
                </span>

                <span
                  className="px-2 py-0.5 rounded-full text-[11px]"
                  style={{
                    background: '#dbeafe',
                    color: '#1d4ed8',
                  }}
                >
                  Security scheme
                </span>

                {Array.isArray(scopes) &&
                  scopes.length > 0 && (
                    <span className="text-[#888]">
                      Scopes:{' '}
                      <span className="font-mono">
                        {scopes.join(' ')}
                      </span>
                    </span>
                  )}
              </div>
            ),
          )}
        </div>
      ))}
    </div>
  )
}

export default function EndpointDetails({
  navigate,
  data,
}: Props) {
  const ep = data as ApiEndpoint | null

  if (!ep) {
    return (
      <div>
        <button
          onClick={() => navigate('explorer')}
          className="flex items-center gap-1.5 text-[13px] text-[#888] mb-5 hover:text-[#1a1a1a] transition-colors"
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontFamily: 'Questrial, sans-serif',
          }}
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
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>

          API Explorer
        </button>

        <div style={{ ...CARD, padding: '24px' }}>
          <div className="text-[15px] font-medium text-[#1a1a1a]">
            Endpoint not found
          </div>

          <div className="text-[13px] text-[#888] mt-1">
            Select an endpoint from the API Explorer.
          </div>
        </div>
      </div>
    )
  }

  const method = ep.method
  const path = ep.path
  const summary = ep.summary ?? 'No summary available'
  const description =
    ep.description ?? 'No description available'

  const sections: Section[] = [
    {
      id: 'params',
      label: 'Parameters',
      content: renderParameters(ep),
    },
    {
      id: 'request',
      label: 'Request body',
      content: renderRequestBody(ep),
    },
    {
      id: 'responses',
      label: 'Responses',
      content: renderResponses(ep),
    },
    {
      id: 'security',
      label: 'Security',
      content: renderSecurity(ep),
    },
  ]

  return (
    <div>
      {/* Back */}
      <button
        onClick={() =>
          navigate('explorer', {
            specificationId: ep.api_specification_id,
          })
        }
        className="flex items-center gap-1.5 text-[13px] text-[#888] mb-5 hover:text-[#1a1a1a] transition-colors"
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'Questrial, sans-serif',
        }}
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
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>

        API Explorer
      </button>

      {/* Endpoint header */}
      <div
        style={{
          ...CARD,
          padding: '20px 24px',
          marginBottom: 16,
        }}
      >
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <MethodBadge method={method} />

              <span className="font-mono text-[18px] text-[#1a1a1a] font-medium">
                {path}
              </span>
            </div>

            <div className="text-[14px] text-[#666]">
              {summary}
            </div>
          </div>

          <div className="flex gap-2">
            <button
              style={{
                background: 'rgba(59,130,246,0.1)',
                color: '#2563eb',
                border: '1px solid rgba(59,130,246,0.2)',
                borderRadius: '12px',
                padding: '7px 16px',
                fontSize: 13,
                cursor: 'pointer',
                fontFamily: 'Questrial, sans-serif',
              }}
              onClick={() => navigate('assistant')}
            >
              Ask AI
            </button>

            <button
              style={{
                background: 'rgba(239,68,68,0.1)',
                color: '#b91c1c',
                border: '1px solid rgba(239,68,68,0.2)',
                borderRadius: '12px',
                padding: '7px 16px',
                fontSize: 13,
                cursor: 'pointer',
                fontFamily: 'Questrial, sans-serif',
              }}
              onClick={() => navigate('debug')}
            >
              Debug
            </button>

            <button
              style={{
                background: 'rgba(34,197,94,0.1)',
                color: '#15803d',
                border: '1px solid rgba(34,197,94,0.2)',
                borderRadius: '12px',
                padding: '7px 16px',
                fontSize: 13,
                cursor: 'pointer',
                fontFamily: 'Questrial, sans-serif',
              }}
              onClick={() => navigate('tests')}
            >
              Generate tests
            </button>
          </div>
        </div>
      </div>

      {/* Description */}
      <div
        style={{
          ...CARD,
          padding: '16px 20px',
          marginBottom: 16,
        }}
      >
        <div className="text-[12px] text-[#aaa] font-medium mb-1">
          Description
        </div>

        <div className="text-[14px] text-[#555]">
          {description}
        </div>
      </div>

      {/* Dynamic metadata */}
      <Accordion sections={sections} />
    </div>
  )
}