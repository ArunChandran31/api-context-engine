import { useEffect, useState } from 'react'
import type { Page } from '../utils'
import { CARD, BTN_PRIMARY, MethodBadge } from '../utils'
import {
  getSpecifications,
  type ApiSpecification,
} from '../api/specifications'
import {
  getEndpoints,
  type ApiEndpoint,
} from '../api/endpoints'
import { generateTestCases } from '../api/testCases'

interface Props {
  navigate: (p: Page) => void
}

type TestStyle = 'jest' | 'pytest' | 'postman' | 'curl'
type TestCategory = 'happy' | 'validation' | 'edge' | 'auth' | 'other'

interface TestCase {
  id: string
  title: string
  category: TestCategory
  description: string
}

const CATEGORY_META: Record<
  TestCategory,
  { label: string; color: string; textColor: string }
> = {
  happy: {
    label: 'Happy path',
    color: '#dcfce7',
    textColor: '#15803d',
  },
  validation: {
    label: 'Validation',
    color: '#fef3c7',
    textColor: '#b45309',
  },
  edge: {
    label: 'Edge case',
    color: '#ede9fe',
    textColor: '#6d28d9',
  },
  auth: {
    label: 'Auth',
    color: '#fee2e2',
    textColor: '#b91c1c',
  },
  other: {
    label: 'Other',
    color: '#f3f4f6',
    textColor: '#4b5563',
  },
}

function normalizeCategory(category: string): TestCategory {
  const value = category.toLowerCase().trim()

  if (
    value.includes('positive') ||
    value.includes('happy') ||
    value.includes('success')
  ) {
    return 'happy'
  }

  if (
    value.includes('negative') ||
    value.includes('validation') ||
    value.includes('invalid')
  ) {
    return 'validation'
  }

  if (
    value.includes('edge') ||
    value.includes('boundary')
  ) {
    return 'edge'
  }

  if (
    value.includes('auth') ||
    value.includes('authorization') ||
    value.includes('authentication')
  ) {
    return 'auth'
  }

  return 'other'
}

function TestCaseRow({ tc }: { tc: TestCase }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const meta = CATEGORY_META[tc.category]

  async function copy() {
    await navigator.clipboard?.writeText(
      `${tc.title}\n\n${tc.description}`,
    )

    setCopied(true)

    setTimeout(() => {
      setCopied(false)
    }, 1500)
  }

  return (
    <div
      style={{
        borderBottom: '1px solid rgba(0,0,0,0.05)',
      }}
    >
      <button
        onClick={() => setOpen((value) => !value)}
        className="w-full flex items-center gap-3 px-5 py-3.5 text-left hover:bg-black/[0.015] transition-colors"
        style={{
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
        }}
      >
        <span
          className="text-[11px] font-medium px-2 py-0.5 rounded-full flex-shrink-0"
          style={{
            background: meta.color,
            color: meta.textColor,
          }}
        >
          {meta.label}
        </span>

        <span className="text-[14px] text-[#1a1a1a] flex-1 text-left">
          {tc.title}
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
            transform: open
              ? 'rotate(180deg)'
              : 'rotate(0)',
            transition: 'transform 200ms',
            flexShrink: 0,
          }}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div className="px-5 pb-4">
          <div className="text-[11px] text-[#aaa] mb-1.5">
            AI-generated test case
          </div>

          <pre
            className="rounded-[12px] p-3 text-[12px] overflow-x-auto leading-relaxed"
            style={{
              background: '#f5f5f5',
              border: '1px solid rgba(0,0,0,0.06)',
              fontFamily: 'JetBrains Mono, monospace',
              whiteSpace: 'pre-wrap',
            }}
          >
            {tc.description}
          </pre>

          <div className="mt-3 flex justify-end">
            <button
              onClick={(event) => {
                event.stopPropagation()
                copy()
              }}
              className="text-[12px] px-3 py-1.5 rounded-[10px] text-[#555] transition-colors"
              style={{
                background: copied
                  ? '#dcfce7'
                  : 'rgba(0,0,0,0.06)',
                color: copied
                  ? '#15803d'
                  : '#555',
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'Questrial, sans-serif',
              }}
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
  const [specifications, setSpecifications] = useState<
    ApiSpecification[]
  >([])

  const [selectedSpecificationId, setSelectedSpecificationId] =
    useState<number | null>(null)

  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>([])
  const [selectedEndpointId, setSelectedEndpointId] =
    useState<number | null>(null)

  const [style, setStyle] = useState<TestStyle>('jest')

  const [categories, setCategories] = useState<TestCategory[]>([
    'happy',
    'validation',
    'edge',
    'auth',
    'other',
  ])

  const [testCases, setTestCases] = useState<TestCase[]>([])
  const [generated, setGenerated] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [loadingEndpoints, setLoadingEndpoints] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /*
   * Load API specifications.
   */
  useEffect(() => {
    async function loadSpecifications() {
      try {
        setError(null)

        const data = await getSpecifications()

        setSpecifications(data)

        if (data.length > 0) {
          setSelectedSpecificationId(data[0].id)
        }
      } catch (error) {
        console.error(
          'Failed to load API specifications:',
          error,
        )

        setError(
          error instanceof Error
            ? error.message
            : 'Failed to load API specifications.',
        )
      }
    }

    loadSpecifications()
  }, [])

  /*
   * Load endpoints whenever the selected API changes.
   */
  useEffect(() => {
    if (selectedSpecificationId === null) {
      setEndpoints([])
      setSelectedEndpointId(null)
      return
    }

    async function loadEndpoints() {
      try {
        setLoadingEndpoints(true)
        setError(null)

        const data = await getEndpoints(
          selectedSpecificationId!,
        )

        setEndpoints(data)

        if (data.length > 0) {
          setSelectedEndpointId(data[0].id)
        } else {
          setSelectedEndpointId(null)
        }

        setGenerated(false)
        setTestCases([])
      } catch (error) {
        console.error(
          'Failed to load API endpoints:',
          error,
        )

        setEndpoints([])
        setSelectedEndpointId(null)

        setError(
          error instanceof Error
            ? error.message
            : 'Failed to load API endpoints.',
        )
      } finally {
        setLoadingEndpoints(false)
      }
    }

    loadEndpoints()
  }, [selectedSpecificationId])

  const selectedEndpoint =
    endpoints.find(
      (endpoint) =>
        endpoint.id === selectedEndpointId,
    ) ?? null

  async function generate() {
    if (
      selectedSpecificationId === null ||
      selectedEndpoint === null ||
      generating
    ) {
      return
    }

    setGenerating(true)
    setGenerated(false)
    setError(null)
    setTestCases([])

    const endpointLabel =
      `${selectedEndpoint.method} ${selectedEndpoint.path}`

    try {
      const result = await generateTestCases(
        `Generate test cases for ${endpointLabel}.`,
        selectedSpecificationId,
        style,
        categories,
      )

      const mappedCases: TestCase[] =
        result.test_cases.map(
          (testCase, index) => ({
            id: `generated-${index + 1}`,
            title:
              `${testCase.category} test case ${index + 1}`,
            category:
              normalizeCategory(
                testCase.category,
              ),
            description:
              testCase.description,
          }),
        )

      setTestCases(mappedCases)
      setGenerated(true)
    } catch (error) {
      console.error(
        'Failed to generate test cases:',
        error,
      )

      setError(
        error instanceof Error
          ? error.message
          : 'Failed to generate test cases.',
      )
    } finally {
      setGenerating(false)
    }
  }

  function toggleCat(cat: TestCategory) {
    setCategories((prev) =>
      prev.includes(cat)
        ? prev.filter(
            (value) => value !== cat,
          )
        : [...prev, cat],
    )
  }

  const filtered = testCases.filter(
    (testCase) =>
      categories.includes(testCase.category),
  )

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-[26px] font-semibold text-[#1a1a1a]">
          Test Case Generator
        </h1>

        <p className="text-[14px] text-[#888] mt-0.5">
          Generate comprehensive test suites from your API schema
        </p>
      </div>

      <div className="grid grid-cols-5 gap-4">

        {/* Left: controls */}
        <div className="col-span-2">
          <div style={{ ...CARD, padding: '20px' }}>
            <div className="flex flex-col gap-4">

              {/* API */}
              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">
                  API
                </label>

                <select
                  value={
                    selectedSpecificationId ?? ''
                  }
                  onChange={(event) => {
                    const value = Number(
                      event.target.value,
                    )

                    setSelectedSpecificationId(
                      value,
                    )

                    setGenerated(false)
                    setTestCases([])
                    setError(null)
                  }}
                  className="w-full rounded-[12px] text-[13px] text-[#1a1a1a]"
                  style={{
                    background:
                      'rgba(255,255,255,0.7)',
                    border:
                      '1px solid rgba(0,0,0,0.1)',
                    padding: '8px 12px',
                    fontFamily:
                      'Questrial, sans-serif',
                    outline: 'none',
                  }}
                >
                  {specifications.map(
                    (specification) => (
                      <option
                        key={specification.id}
                        value={specification.id}
                      >
                        {specification.title}
                      </option>
                    ),
                  )}
                </select>
              </div>

              {/* Endpoint */}
              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">
                  Endpoint
                </label>

                <select
                  value={
                    selectedEndpointId ?? ''
                  }
                  onChange={(event) => {
                    setSelectedEndpointId(
                      Number(
                        event.target.value,
                      ),
                    )

                    setGenerated(false)
                    setTestCases([])
                    setError(null)
                  }}
                  disabled={
                    loadingEndpoints ||
                    endpoints.length === 0
                  }
                  className="w-full rounded-[12px] text-[13px] text-[#1a1a1a]"
                  style={{
                    background:
                      'rgba(255,255,255,0.7)',
                    border:
                      '1px solid rgba(0,0,0,0.1)',
                    padding: '8px 12px',
                    fontFamily:
                      'JetBrains Mono, monospace',
                    outline: 'none',
                  }}
                >
                  {loadingEndpoints && (
                    <option>
                      Loading endpoints...
                    </option>
                  )}

                  {!loadingEndpoints &&
                    endpoints.length === 0 && (
                      <option>
                        No endpoints available
                      </option>
                    )}

                  {!loadingEndpoints &&
                    endpoints.map(
                      (endpoint) => (
                        <option
                          key={endpoint.id}
                          value={endpoint.id}
                        >
                          {endpoint.method}{' '}
                          {endpoint.path}
                        </option>
                      ),
                    )}
                </select>
              </div>

              {/* Test style */}
              <div>
                <label className="text-[12px] text-[#888] block mb-1.5">
                  Test style
                </label>

                <div className="grid grid-cols-2 gap-1.5">
                  {(
                    [
                      'jest',
                      'pytest',
                      'postman',
                      'curl',
                    ] as TestStyle[]
                  ).map((testStyle) => (
                    <button
                      key={testStyle}
                      onClick={() =>
                        setStyle(testStyle)
                      }
                      className="py-2 rounded-[10px] text-[13px] capitalize transition-all"
                      style={{
                        background:
                          style === testStyle
                            ? '#1a1a1a'
                            : 'rgba(0,0,0,0.04)',
                        color:
                          style === testStyle
                            ? '#fff'
                            : '#555',
                        border: 'none',
                        cursor: 'pointer',
                        fontFamily:
                          'Questrial, sans-serif',
                      }}
                    >
                      {testStyle}
                    </button>
                  ))}
                </div>
              </div>

              {/* Generation options */}
              <div>
                <label className="text-[12px] text-[#888] block mb-2">
                  Generation options
                </label>

                <div className="flex flex-col gap-2">
                  {(
                    Object.entries(
                      CATEGORY_META,
                    ) as [
                      TestCategory,
                      typeof CATEGORY_META[TestCategory],
                    ][]
                  ).map(([cat, meta]) => (
                    <label
                      key={cat}
                      className="flex items-center gap-2.5 cursor-pointer"
                    >
                      <div
                        onClick={() =>
                          toggleCat(cat)
                        }
                        className="w-4 h-4 rounded-[5px] flex items-center justify-center flex-shrink-0"
                        style={{
                          background:
                            categories.includes(
                              cat,
                            )
                              ? '#1a1a1a'
                              : 'rgba(0,0,0,0.08)',
                          border:
                            categories.includes(
                              cat,
                            )
                              ? 'none'
                              : '1px solid rgba(0,0,0,0.1)',
                          cursor: 'pointer',
                        }}
                      >
                        {categories.includes(
                          cat,
                        ) && (
                          <svg
                            width={10}
                            height={10}
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="white"
                            strokeWidth={3}
                            strokeLinecap="round"
                          >
                            <path d="M20 6L9 17l-5-5" />
                          </svg>
                        )}
                      </div>

                      <span
                        className="text-[11px] px-2 py-0.5 rounded-full font-medium"
                        style={{
                          background:
                            meta.color,
                          color:
                            meta.textColor,
                        }}
                      >
                        {meta.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Error */}
              {error && (
                <div
                  className="rounded-[12px] px-3 py-2 text-[12px]"
                  style={{
                    background: '#fee2e2',
                    color: '#b91c1c',
                    border:
                      '1px solid rgba(185,28,28,0.12)',
                  }}
                >
                  {error}
                </div>
              )}

              {/* Generate */}
              <button
                style={{
                  ...BTN_PRIMARY,
                  width: '100%',
                  justifyContent: 'center',
                  opacity: generating
                    ? 0.7
                    : 1,
                }}
                onClick={generate}
                disabled={
                  generating ||
                  selectedEndpoint === null
                }
              >
                {generating ? (
                  <>
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                    Generating...
                  </>
                ) : (
                  'Generate test cases'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right: results */}
        <div className="col-span-3">

          {!generated && !generating && (
            <div
              className="flex flex-col items-center justify-center rounded-[20px] text-center"
              style={{
                ...CARD,
                minHeight: 300,
              }}
            >
              <svg
                width={40}
                height={40}
                viewBox="0 0 24 24"
                fill="none"
                stroke="#ddd"
                strokeWidth={1.5}
                strokeLinecap="round"
                className="mb-3"
              >
                <path d="M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </svg>

              <div className="text-[14px] text-[#ccc]">
                Configure and generate
                <br />
                to see test cases here
              </div>
            </div>
          )}

          {generating && (
            <div
              className="flex flex-col items-center justify-center rounded-[20px]"
              style={{
                ...CARD,
                minHeight: 300,
              }}
            >
              <div className="w-8 h-8 rounded-full border-2 border-black/10 border-t-black/70 animate-spin mb-3" />

              <div className="text-[14px] text-[#888]">
                Generating test cases...
              </div>
            </div>
          )}

          {generated && selectedEndpoint && (
            <div
              style={{
                ...CARD,
                padding: 0,
                overflow: 'hidden',
              }}
            >
              <div
                className="px-5 py-3.5 flex items-center justify-between"
                style={{
                  borderBottom:
                    '1px solid rgba(0,0,0,0.06)',
                }}
              >
                <div className="flex items-center gap-3">
                  <MethodBadge
                    method={selectedEndpoint.method}
                  />

                  <span className="font-mono text-[13px] text-[#1a1a1a]">
                    {selectedEndpoint.path}
                  </span>
                </div>

                <span className="text-[12px] text-[#aaa]">
                  {filtered.length} test cases ·{' '}
                  {style}
                </span>
              </div>

              {filtered.map((testCase) => (
                <TestCaseRow
                  key={testCase.id}
                  tc={testCase}
                />
              ))}

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