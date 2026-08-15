import type { Page } from '../utils'
import { CARD } from '../utils'

interface Props { navigate: (p: Page) => void }

type ServiceStatus = 'Healthy' | 'Configured' | 'Degraded' | 'Error'

interface Service {
  name: string
  status: ServiceStatus
  detail: string
}

const SERVICES: Service[] = [
  { name: 'API service',   status: 'Healthy',    detail: 'Responding normally' },
  { name: 'Database',      status: 'Healthy',    detail: 'PostgreSQL 15.4 · 4ms latency' },
  { name: 'Redis cache',   status: 'Healthy',    detail: '23MB / 512MB used' },
  { name: 'Vector store',  status: 'Configured', detail: 'Chroma · 42 embeddings indexed' },
  { name: 'LLM provider',  status: 'Configured', detail: 'Groq · llama3-8b-8192' },
]

const STATUS_COLORS: Record<ServiceStatus, { bg: string; text: string; dot: string }> = {
  Healthy:    { bg: '#dcfce7', text: '#15803d', dot: '#22c55e' },
  Configured: { bg: '#dbeafe', text: '#1d4ed8', dot: '#3b82f6' },
  Degraded:   { bg: '#fef3c7', text: '#b45309', dot: '#f59e0b' },
  Error:      { bg: '#fee2e2', text: '#b91c1c', dot: '#ef4444' },
}

function StatusPill({ status }: { status: ServiceStatus }) {
  const c = STATUS_COLORS[status]
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-medium" style={{ background: c.bg, color: c.text }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: c.dot }} />
      {status}
    </span>
  )
}

const PIPELINE_STAGES = [
  { id: 'ingest',   label: 'Ingest',    status: 'Healthy' as ServiceStatus },
  { id: 'chunk',    label: 'Chunk',     status: 'Healthy' as ServiceStatus },
  { id: 'embed',    label: 'Embed',     status: 'Configured' as ServiceStatus },
  { id: 'index',    label: 'Index',     status: 'Configured' as ServiceStatus },
  { id: 'retrieve', label: 'Retrieve',  status: 'Healthy' as ServiceStatus },
]

export default function SystemStatus({ navigate }: Props) {
  const allHealthy = SERVICES.every(s => s.status === 'Healthy' || s.status === 'Configured')
  const overallStatus: ServiceStatus = allHealthy ? 'Healthy' : 'Degraded'

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-[26px] font-semibold text-[#1a1a1a]">System Status</h1>
          <p className="text-[14px] text-[#888] mt-0.5">Service health and infrastructure overview</p>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <StatusPill status={overallStatus} />
        </div>
      </div>

      {/* Services */}
      <div className="mb-4">
        <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">Services</div>
        <div style={{ ...CARD, padding: 0, overflow: 'hidden' }}>
          {SERVICES.map((svc, i) => (
            <div
              key={svc.name}
              className="flex items-center justify-between px-5 py-4"
              style={i < SERVICES.length - 1 ? { borderBottom: '1px solid rgba(0,0,0,0.05)' } : {}}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-[10px] flex items-center justify-center"
                  style={{ background: STATUS_COLORS[svc.status].bg }}
                >
                  <div className="w-2 h-2 rounded-full" style={{ background: STATUS_COLORS[svc.status].dot }} />
                </div>
                <div>
                  <div className="text-[14px] font-medium text-[#1a1a1a]">{svc.name}</div>
                  <div className="text-[12px] text-[#aaa] mt-0.5">{svc.detail}</div>
                </div>
              </div>
              <StatusPill status={svc.status} />
            </div>
          ))}
        </div>
      </div>

      {/* RAG Pipeline */}
      <div>
        <div className="text-[12px] font-semibold text-[#aaa] uppercase tracking-wider mb-3">RAG pipeline</div>
        <div style={{ ...CARD, padding: '24px' }}>
          <div className="flex items-center gap-0">
            {PIPELINE_STAGES.map((stage, i) => {
              const c = STATUS_COLORS[stage.status]
              return (
                <div key={stage.id} className="flex items-center flex-1">
                  {/* Stage node */}
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center mb-2"
                      style={{ background: c.bg, border: `2px solid ${c.dot}` }}
                    >
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background: c.dot }} />
                    </div>
                    <div className="text-[13px] font-medium text-[#1a1a1a] text-center">{stage.label}</div>
                    <StatusPill status={stage.status} />
                  </div>

                  {/* Connector arrow */}
                  {i < PIPELINE_STAGES.length - 1 && (
                    <div className="flex items-center flex-shrink-0 px-1 pb-7">
                      <div className="h-px w-6" style={{ background: 'rgba(0,0,0,0.12)' }} />
                      <svg width={8} height={12} viewBox="0 0 8 12" fill="none" className="flex-shrink-0">
                        <path d="M1 1l6 5-6 5" stroke="rgba(0,0,0,0.2)" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Pipeline detail */}
          <div
            className="mt-5 rounded-[14px] p-4 text-[13px] text-[#555] leading-relaxed"
            style={{ background: 'rgba(0,0,0,0.03)', border: '1px solid rgba(0,0,0,0.05)' }}
          >
            <span className="font-medium text-[#1a1a1a]">Pipeline summary:</span> Specifications are ingested from file or URL, chunked by endpoint and schema, embedded using the configured LLM provider, indexed in the vector store, and retrieved via semantic search during AI queries.
          </div>
        </div>
      </div>
    </div>
  )
}
