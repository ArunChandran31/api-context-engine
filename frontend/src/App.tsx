import { useState, useRef } from 'react'
import type { Page } from './utils'
import { GLASS } from './utils'
import Dashboard from './pages/Dashboard'
import UploadSpec from './pages/UploadSpec'
import APIExplorer from './pages/APIExplorer'
import EndpointDetails from './pages/EndpointDetails'
import AIAssistant from './pages/AIAssistant'
import DebugAssistant from './pages/DebugAssistant'
import TestCases from './pages/TestCases'
import SystemStatus from './pages/SystemStatus'
import Settings from './pages/Settings'

// ── Icons ────────────────────────────────────────────────────────────────────
function Ico({ d, size = 18 }: { d: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  )
}

const NAV_ITEMS: { id: Page; label: string; paths: string[] }[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    paths: [
      'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
    ],
  },
  {
    id: 'explorer',
    label: 'API Explorer',
    paths: ['M12 2L2 7l10 5 10-5-10-5', 'M2 17l10 5 10-5', 'M2 12l10 5 10-5'],
  },
  {
    id: 'assistant',
    label: 'AI Assistant',
    paths: ['M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z'],
  },
  {
    id: 'debug',
    label: 'Debug Assistant',
    paths: [
      'M12 20h.01',
      'M8 2l-2 4h12l-2-4',
      'M5 6a7 7 0 1014 0',
      'M9 14h6',
      'M12 11v6',
    ],
  },
  {
    id: 'tests',
    label: 'Test Cases',
    paths: ['M9 11l3 3L22 4', 'M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11'],
  },
  {
    id: 'status',
    label: 'System Status',
    paths: ['M22 12h-4l-3 9L9 3l-3 9H2'],
  },
  {
    id: 'settings',
    label: 'Settings',
    paths: [
      'M12 15a3 3 0 100-6 3 3 0 000 6z',
      'M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z',
    ],
  },
]

function NavIcon({ paths }: { paths: string[] }) {
  return (
    <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      {paths.map((d, i) => <path key={i} d={d} />)}
    </svg>
  )
}

// ── Profile dropdown ─────────────────────────────────────────────────────────
function ProfileMenu({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="absolute right-0 top-10 z-50 w-44 py-1.5"
      style={{
        ...GLASS,
        borderRadius: '16px',
        boxShadow: '0 12px 40px rgba(0,0,0,0.12)',
      }}
      onMouseLeave={onClose}
    >
      {['Account', 'Preferences', 'Sign out'].map((item) => (
        <button
          key={item}
          className="w-full text-left px-4 py-2 text-sm text-[#1a1a1a] hover:bg-black/5 transition-colors"
          style={{ fontFamily: 'Questrial, sans-serif' }}
        >
          {item}
        </button>
      ))}
    </div>
  )
}

// ── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar({
  open,
  onToggle,
  current,
  navigate,
}: {
  open: boolean
  onToggle: () => void
  current: Page
  navigate: (p: Page) => void
}) {
  return (
    <aside
      className="fixed z-40 flex flex-col"
      style={{
        ...GLASS,
        left: 12,
        top: 72,
        bottom: 12,
        width: open ? 220 : 64,
        transition: 'width 280ms cubic-bezier(0.4,0,0.2,1)',
        overflow: 'hidden',
      }}
    >
      {/* Nav items */}
      <nav className="flex-1 flex flex-col gap-1 p-2 mt-1">
        {NAV_ITEMS.map((item) => {
          const active = current === item.id
          return (
            <button
              key={item.id}
              onClick={() => navigate(item.id)}
              title={!open ? item.label : undefined}
              className="flex items-center gap-3 px-3 py-2.5 rounded-[14px] text-sm text-left"
              style={{
                background: active ? 'rgba(26,26,26,0.08)' : 'transparent',
                color: active ? '#1a1a1a' : '#666',
                fontFamily: 'Questrial, sans-serif',
                fontWeight: active ? 600 : 400,
                cursor: 'pointer',
                border: 'none',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
              }}
            >
              <span className="flex-shrink-0" style={{ color: active ? '#1a1a1a' : '#888' }}>
                <NavIcon paths={item.paths} />
              </span>
              <span
                style={{
                  opacity: open ? 1 : 0,
                  transition: 'opacity 200ms',
                  transitionDelay: open ? '80ms' : '0ms',
                }}
              >
                {item.label}
              </span>
            </button>
          )
        })}
      </nav>

      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="mx-auto mb-3 flex items-center justify-center rounded-full"
        style={{
          width: 32,
          height: 32,
          background: 'rgba(0,0,0,0.06)',
          border: 'none',
          cursor: 'pointer',
          color: '#666',
          flexShrink: 0,
        }}
      >
        <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
          {open ? <path d="M15 18l-6-6 6-6" /> : <path d="M9 18l6-6-6-6" />}
        </svg>
      </button>
    </aside>
  )
}

// ── Header ───────────────────────────────────────────────────────────────────
function Header({ navigate }: { navigate: (p: Page) => void }) {
  const [profileOpen, setProfileOpen] = useState(false)

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-5"
      style={{ height: 60 }}
    >
      {/* Logo area */}
      <div className="flex items-center gap-3">
        {/* Logo placeholder */}
        <div
          className="flex items-center justify-center rounded-[10px]"
          style={{
            width: 32,
            height: 32,
            background: '#1a1a1a',
          }}
        >
          <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2} strokeLinecap="round">
            <path d="M4 7h16M4 12h10M4 17h13" />
          </svg>
        </div>
        <div>
          <div className="text-[15px] font-semibold text-[#1a1a1a] leading-none">ContextAPI</div>
          <div className="text-[11px] text-[#888] mt-0.5">API Context Engine</div>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-[12px] text-[13px] text-[#555]"
          style={{ background: 'rgba(255,255,255,0.6)', border: '1px solid rgba(0,0,0,0.08)', cursor: 'pointer', fontFamily: 'Questrial, sans-serif' }}
        >
          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
            <circle cx="12" cy="17" r="0.5" fill="currentColor" />
          </svg>
          Help
        </button>

        {/* Profile */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen((v) => !v)}
            className="flex items-center gap-2 px-2 py-1 rounded-[12px]"
            style={{ background: 'rgba(255,255,255,0.6)', border: '1px solid rgba(0,0,0,0.08)', cursor: 'pointer' }}
          >
            <div
              className="rounded-full flex items-center justify-center text-white text-[12px] font-semibold"
              style={{ width: 28, height: 28, background: 'linear-gradient(135deg, #1a1a1a, #555)' }}
            >
              JD
            </div>
            <span className="text-[13px] text-[#333] pr-1" style={{ fontFamily: 'Questrial, sans-serif' }}>James</span>
            <svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth={2} strokeLinecap="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>
          {profileOpen && <ProfileMenu onClose={() => setProfileOpen(false)} />}
        </div>
      </div>
    </header>
  )
}

// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [pageData, setPageData] = useState<unknown>(null)
  const mainRef = useRef<HTMLDivElement>(null)

  const navigate = (p: Page, data?: unknown) => {
    setPage(p)
    setPageData(data ?? null)
    // Reset scroll to top on every navigation without affecting sidebar
    if (mainRef.current) mainRef.current.scrollTop = 0
  }

  const sidebarW = sidebarOpen ? 220 : 64
  // Left edge of main content: sidebar left(12) + sidebar width + gap(12)
  const mainLeft = 12 + sidebarW + 12

  const pageProps = { navigate }

  function renderPage() {
    switch (page) {
      case 'dashboard':  return <Dashboard {...pageProps} />
      case 'upload':     return <UploadSpec {...pageProps} />
      case 'explorer':   return <APIExplorer {...pageProps} data={pageData} />
      case 'endpoint':   return <EndpointDetails {...pageProps} data={pageData} />
      case 'assistant':  return <AIAssistant {...pageProps} />
      case 'debug':      return <DebugAssistant {...pageProps} />
      case 'tests':      return <TestCases {...pageProps} />
      case 'status':     return <SystemStatus {...pageProps} />
      case 'settings':   return <Settings {...pageProps} />
      default:           return <Dashboard {...pageProps} />
    }
  }

  return (
    <div style={{ background: '#EFEFEF', height: '100vh', overflow: 'hidden' }}>
      {/* Global header — always fixed, always same position */}
      <Header navigate={navigate} />

      {/* Global sidebar — always fixed, never moves */}
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen((v) => !v)}
        current={page}
        navigate={navigate}
      />

      {/*
        Main content: fixed so it never interacts with document scroll.
        Has its own overflow-y: auto so only the content region scrolls.
        scrollTop is reset to 0 on every navigate() call.
        AI Assistant gets full height via height: 100% on its root div.
      */}
      <main
        ref={mainRef}
        style={{
          position: 'fixed',
          top: 60,
          left: mainLeft,
          right: 0,
          bottom: 0,
          overflowY: 'auto',
          overflowX: 'hidden',
          transition: 'left 280ms cubic-bezier(0.4,0,0.2,1)',
        }}
      >
        {/* Centered content wrapper — shared by every page */}
        <div
          style={{
            width: '100%',
            maxWidth: 1100,
            margin: '0 auto',
            padding: '28px 32px 48px',
            height: page === 'assistant' ? '100%' : undefined,
            boxSizing: 'border-box',
          }}
        >
          {renderPage()}
        </div>
      </main>
    </div>
  )
}
