import { useState } from "react"
import { supabase } from "../lib/supabase"

type AuthState = "idle" | "loading" | "error"
type TabId = 0 | 1 | 2

const FONT = "'DM Sans', 'Google Sans', 'Roboto', sans-serif"
const MONO = "'JetBrains Mono', 'Fira Code', 'Menlo', monospace"

const TABS = [
  {
    headline: "Understand your APIs.",
    sub: "Explore endpoints, schemas, parameters, and relationships with complete API context.",
  },
  {
    headline: "Find what went wrong.",
    sub: "Trace API failures and understand the context behind every error.",
  },
  {
    headline: "Build with confidence.",
    sub: "Generate meaningful API test scenarios from your specification and context.",
  },
] as const

// ─── Google icon ──────────────────────────────────────────────────────────────

function GoogleGlyph() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  )
}

// ─── EXPLORE canvas ───────────────────────────────────────────────────────────

function ExploreCanvas({ visible }: { visible: boolean }) {
  return (
    <svg
      className="absolute inset-0 w-full h-full"
      viewBox="0 0 520 560"
      fill="none"
      preserveAspectRatio="xMidYMid slice"
      style={{
        opacity: visible ? 1 : 0,
        transition: "opacity 420ms ease-in-out",
        pointerEvents: "none",
      }}
    >
      <defs>
        <pattern
          id="grid-e"
          x="0"
          y="0"
          width="28"
          height="28"
          patternUnits="userSpaceOnUse"
        >
          <circle cx="1" cy="1" r="0.8" fill="rgba(255,255,255,0.07)" />
        </pattern>
        <radialGradient id="blob-blue-e" cx="38%" cy="44%" r="52%">
          <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.17" />
          <stop offset="100%" stopColor="#3B82F6" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="blob-green-e" cx="68%" cy="64%" r="48%">
          <stop offset="0%" stopColor="#10B981" stopOpacity="0.11" />
          <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
        </radialGradient>
        <filter id="glow-e" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <rect width="520" height="560" fill="url(#grid-e)" />
      <ellipse cx="200" cy="270" rx="230" ry="210" fill="url(#blob-blue-e)" />
      <ellipse cx="370" cy="390" rx="190" ry="175" fill="url(#blob-green-e)" />

      {/* Connection lines with animated dash flow */}
      <line
        x1="105"
        y1="195"
        x2="258"
        y2="288"
        stroke="rgba(99,160,255,0.18)"
        strokeWidth="1"
        strokeDasharray="5 4"
      >
        <animate
          attributeName="stroke-dashoffset"
          from="36"
          to="0"
          dur="3.2s"
          repeatCount="indefinite"
        />
      </line>
      <line
        x1="258"
        y1="288"
        x2="392"
        y2="218"
        stroke="rgba(99,160,255,0.15)"
        strokeWidth="1"
        strokeDasharray="5 4"
      >
        <animate
          attributeName="stroke-dashoffset"
          from="36"
          to="0"
          dur="4.1s"
          repeatCount="indefinite"
        />
      </line>
      <line
        x1="258"
        y1="288"
        x2="328"
        y2="400"
        stroke="rgba(52,211,153,0.14)"
        strokeWidth="1"
        strokeDasharray="5 4"
      >
        <animate
          attributeName="stroke-dashoffset"
          from="36"
          to="0"
          dur="3.6s"
          repeatCount="indefinite"
        />
      </line>
      <line
        x1="392"
        y1="218"
        x2="468"
        y2="332"
        stroke="rgba(99,160,255,0.11)"
        strokeWidth="1"
      />
      <line
        x1="328"
        y1="400"
        x2="468"
        y2="332"
        stroke="rgba(52,211,153,0.11)"
        strokeWidth="1"
      />
      <line
        x1="105"
        y1="195"
        x2="158"
        y2="358"
        stroke="rgba(148,163,184,0.09)"
        strokeWidth="0.75"
      />
      <line
        x1="158"
        y1="358"
        x2="328"
        y2="400"
        stroke="rgba(148,163,184,0.08)"
        strokeWidth="0.75"
      />
      <line
        x1="392"
        y1="218"
        x2="444"
        y2="170"
        stroke="rgba(99,160,255,0.09)"
        strokeWidth="0.75"
      />

      {/* Nodes — pulsing halo + core */}
      <g>
        <circle cx="105" cy="195" r="8" fill="rgba(59,130,246,0.08)">
          <animate
            attributeName="r"
            values="7;12;7"
            dur="4s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.08;0.16;0.08"
            dur="4s"
            repeatCount="indefinite"
          />
        </circle>
        <circle
          cx="105"
          cy="195"
          r="4.5"
          fill="rgba(99,160,255,0.6)"
          filter="url(#glow-e)"
        >
          <animate
            attributeName="opacity"
            values="0.6;0.92;0.6"
            dur="4s"
            repeatCount="indefinite"
          />
        </circle>
      </g>
      <g>
        <circle cx="258" cy="288" r="14" fill="rgba(59,130,246,0.07)">
          <animate
            attributeName="r"
            values="11;18;11"
            dur="5.2s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.07;0.14;0.07"
            dur="5.2s"
            repeatCount="indefinite"
          />
        </circle>
        <circle
          cx="258"
          cy="288"
          r="6"
          fill="rgba(99,160,255,0.68)"
          filter="url(#glow-e)"
        >
          <animate
            attributeName="opacity"
            values="0.68;1;0.68"
            dur="5.2s"
            repeatCount="indefinite"
          />
        </circle>
      </g>
      <g>
        <circle cx="392" cy="218" r="8" fill="rgba(16,185,129,0.08)">
          <animate
            attributeName="r"
            values="7;11;7"
            dur="3.7s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.08;0.15;0.08"
            dur="3.7s"
            repeatCount="indefinite"
          />
        </circle>
        <circle
          cx="392"
          cy="218"
          r="4.5"
          fill="rgba(52,211,153,0.58)"
          filter="url(#glow-e)"
        >
          <animate
            attributeName="opacity"
            values="0.58;0.9;0.58"
            dur="3.7s"
            repeatCount="indefinite"
          />
        </circle>
      </g>
      <circle
        cx="328"
        cy="400"
        r="4.5"
        fill="rgba(99,160,255,0.44)"
        filter="url(#glow-e)"
      />
      <circle
        cx="468"
        cy="332"
        r="4"
        fill="rgba(52,211,153,0.4)"
        filter="url(#glow-e)"
      />
      <circle cx="158" cy="358" r="3.2" fill="rgba(148,163,184,0.32)" />
      <circle cx="444" cy="170" r="3" fill="rgba(99,160,255,0.28)" />

      {/* Endpoint labels */}
      <text
        x="118"
        y="164"
        fill="rgba(99,160,255,0.36)"
        fontSize="8.5"
        fontFamily={MONO}
      >
        GET /api/v1/context
      </text>
      <text
        x="272"
        y="260"
        fill="rgba(148,163,184,0.26)"
        fontSize="8"
        fontFamily={MONO}
      >
        POST /endpoints
      </text>
      <text
        x="403"
        y="192"
        fill="rgba(52,211,153,0.3)"
        fontSize="8.5"
        fontFamily={MONO}
      >
        {"{ status: 200 }"}
      </text>
      <text
        x="50"
        y="295"
        fill="rgba(148,163,184,0.13)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        Authorization: Bearer
      </text>
      <text
        x="185"
        y="440"
        fill="rgba(148,163,184,0.18)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        schema: OpenAPI 3.1
      </text>
      <text
        x="430"
        y="390"
        fill="rgba(148,163,184,0.14)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        latency: 9ms
      </text>

      {/* Schema card */}
      <rect
        x="415"
        y="260"
        width="72"
        height="54"
        rx="5"
        fill="rgba(255,255,255,0.025)"
        stroke="rgba(255,255,255,0.07)"
        strokeWidth="0.75"
      />
      <line
        x1="426"
        y1="276"
        x2="476"
        y2="276"
        stroke="rgba(255,255,255,0.1)"
        strokeWidth="0.5"
      />
      <line
        x1="426"
        y1="286"
        x2="468"
        y2="286"
        stroke="rgba(255,255,255,0.07)"
        strokeWidth="0.5"
      />
      <line
        x1="426"
        y1="296"
        x2="474"
        y2="296"
        stroke="rgba(255,255,255,0.07)"
        strokeWidth="0.5"
      />
      <line
        x1="426"
        y1="306"
        x2="464"
        y2="306"
        stroke="rgba(255,255,255,0.05)"
        strokeWidth="0.5"
      />

      <rect
        x="46"
        y="212"
        width="52"
        height="40"
        rx="5"
        fill="rgba(255,255,255,0.02)"
        stroke="rgba(255,255,255,0.055)"
        strokeWidth="0.75"
      />
      <line
        x1="55"
        y1="225"
        x2="88"
        y2="225"
        stroke="rgba(255,255,255,0.09)"
        strokeWidth="0.5"
      />
      <line
        x1="55"
        y1="234"
        x2="83"
        y2="234"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="0.5"
      />
      <line
        x1="55"
        y1="243"
        x2="87"
        y2="243"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="0.5"
      />
    </svg>
  )
}

// ─── DEBUG canvas ─────────────────────────────────────────────────────────────

function DebugCanvas({ visible }: { visible: boolean }) {
  return (
    <svg
      className="absolute inset-0 w-full h-full"
      viewBox="0 0 520 560"
      fill="none"
      preserveAspectRatio="xMidYMid slice"
      style={{
        opacity: visible ? 1 : 0,
        transition: "opacity 420ms ease-in-out",
        pointerEvents: "none",
      }}
    >
      <defs>
        <pattern
          id="grid-d"
          x="0"
          y="0"
          width="28"
          height="28"
          patternUnits="userSpaceOnUse"
        >
          <circle cx="1" cy="1" r="0.8" fill="rgba(255,255,255,0.06)" />
        </pattern>
        <radialGradient id="blob-red-d" cx="50%" cy="50%" r="52%">
          <stop offset="0%" stopColor="#EF4444" stopOpacity="0.13" />
          <stop offset="100%" stopColor="#EF4444" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="blob-amber-d" cx="62%" cy="38%" r="44%">
          <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.09" />
          <stop offset="100%" stopColor="#F59E0B" stopOpacity="0" />
        </radialGradient>
        <filter id="glow-d" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <rect width="520" height="560" fill="url(#grid-d)" />
      <ellipse cx="270" cy="300" rx="220" ry="195" fill="url(#blob-red-d)" />
      <ellipse cx="370" cy="200" rx="160" ry="140" fill="url(#blob-amber-d)" />

      {/* Main trace flow: REQUEST → ROUTING → ERROR → FAILED */}
      <text
        x="56"
        y="172"
        fill="rgba(148,163,184,0.22)"
        fontSize="8.5"
        fontFamily={MONO}
      >
        POST /api/orders/confirm
      </text>

      {/* Horizontal trace line */}
      <line
        x1="72"
        y1="225"
        x2="212"
        y2="225"
        stroke="rgba(148,163,184,0.22)"
        strokeWidth="1.5"
        strokeDasharray="5 3"
      >
        <animate
          attributeName="stroke-dashoffset"
          from="32"
          to="0"
          dur="2.2s"
          repeatCount="indefinite"
        />
      </line>
      <line
        x1="212"
        y1="225"
        x2="328"
        y2="225"
        stroke="rgba(245,158,11,0.26)"
        strokeWidth="1.5"
        strokeDasharray="5 3"
      >
        <animate
          attributeName="stroke-dashoffset"
          from="32"
          to="0"
          dur="2.6s"
          repeatCount="indefinite"
        />
      </line>
      <line
        x1="328"
        y1="225"
        x2="448"
        y2="225"
        stroke="rgba(239,68,68,0.32)"
        strokeWidth="1.5"
        strokeDasharray="5 3"
      >
        <animate
          attributeName="stroke-dashoffset"
          from="32"
          to="0"
          dur="2s"
          repeatCount="indefinite"
        />
      </line>

      {/* Vertical trace branches */}
      <line
        x1="212"
        y1="225"
        x2="212"
        y2="345"
        stroke="rgba(148,163,184,0.1)"
        strokeWidth="1"
      />
      <line
        x1="212"
        y1="345"
        x2="328"
        y2="388"
        stroke="rgba(239,68,68,0.14)"
        strokeWidth="1"
      />
      <line
        x1="328"
        y1="225"
        x2="328"
        y2="388"
        stroke="rgba(239,68,68,0.09)"
        strokeWidth="0.75"
      />

      {/* REQUEST node */}
      <circle cx="72" cy="225" r="11" fill="rgba(148,163,184,0.07)" />
      <circle cx="72" cy="225" r="5.5" fill="rgba(148,163,184,0.42)" />
      <text
        x="50"
        y="250"
        fill="rgba(148,163,184,0.38)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        REQUEST
      </text>

      {/* ROUTING node */}
      <circle cx="212" cy="225" r="13" fill="rgba(245,158,11,0.07)" />
      <circle
        cx="212"
        cy="225"
        r="6.5"
        fill="rgba(245,158,11,0.52)"
        filter="url(#glow-d)"
      >
        <animate
          attributeName="opacity"
          values="0.52;0.82;0.52"
          dur="2.1s"
          repeatCount="indefinite"
        />
      </circle>
      <text
        x="194"
        y="250"
        fill="rgba(245,158,11,0.38)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        ROUTING
      </text>

      {/* ERROR node — pulsing red */}
      <g>
        <circle cx="328" cy="225" r="16" fill="rgba(239,68,68,0.08)">
          <animate
            attributeName="r"
            values="13;20;13"
            dur="2.8s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.08;0.15;0.08"
            dur="2.8s"
            repeatCount="indefinite"
          />
        </circle>
        <circle
          cx="328"
          cy="225"
          r="7.5"
          fill="rgba(239,68,68,0.68)"
          filter="url(#glow-d)"
        >
          <animate
            attributeName="opacity"
            values="0.68;1;0.68"
            dur="2.8s"
            repeatCount="indefinite"
          />
        </circle>
      </g>
      <text
        x="313"
        y="210"
        fill="rgba(239,68,68,0.6)"
        fontSize="8.5"
        fontFamily={MONO}
      >
        500
      </text>

      {/* FAILED node */}
      <circle cx="448" cy="225" r="9" fill="rgba(239,68,68,0.05)" />
      <circle cx="448" cy="225" r="4.5" fill="rgba(239,68,68,0.32)" />
      <text
        x="430"
        y="250"
        fill="rgba(239,68,68,0.28)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        FAILED
      </text>

      {/* DIAGNOSIS node */}
      <circle cx="328" cy="388" r="11" fill="rgba(99,160,255,0.06)" />
      <circle cx="328" cy="388" r="5" fill="rgba(99,160,255,0.38)" />
      <text
        x="308"
        y="412"
        fill="rgba(99,160,255,0.32)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        DIAGNOSIS
      </text>

      {/* HTTP status code badges */}
      <rect
        x="378"
        y="295"
        width="70"
        height="22"
        rx="4"
        fill="rgba(239,68,68,0.08)"
        stroke="rgba(239,68,68,0.22)"
        strokeWidth="0.75"
      />
      <text
        x="390"
        y="310"
        fill="rgba(239,68,68,0.56)"
        fontSize="9.5"
        fontFamily={MONO}
        fontWeight="600"
      >
        500 ISE
      </text>

      <rect
        x="378"
        y="325"
        width="70"
        height="22"
        rx="4"
        fill="rgba(245,158,11,0.07)"
        stroke="rgba(245,158,11,0.2)"
        strokeWidth="0.75"
      />
      <text
        x="390"
        y="340"
        fill="rgba(245,158,11,0.5)"
        fontSize="9.5"
        fontFamily={MONO}
        fontWeight="600"
      >
        422 UPE
      </text>

      <rect
        x="378"
        y="355"
        width="70"
        height="22"
        rx="4"
        fill="rgba(239,68,68,0.06)"
        stroke="rgba(239,68,68,0.16)"
        strokeWidth="0.75"
      />
      <text
        x="390"
        y="370"
        fill="rgba(239,68,68,0.42)"
        fontSize="9.5"
        fontFamily={MONO}
        fontWeight="600"
      >
        404 NF
      </text>

      {/* Trace log panel */}
      <rect
        x="44"
        y="278"
        width="146"
        height="84"
        rx="6"
        fill="rgba(255,255,255,0.025)"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="0.75"
      />
      <text
        x="56"
        y="296"
        fill="rgba(148,163,184,0.34)"
        fontSize="8"
        fontFamily={MONO}
      >
        TRACE LOG
      </text>
      <line
        x1="56"
        y1="303"
        x2="181"
        y2="303"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="0.5"
      />
      <text
        x="56"
        y="317"
        fill="rgba(52,211,153,0.38)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        → auth.middleware: PASS
      </text>
      <text
        x="56"
        y="330"
        fill="rgba(245,158,11,0.38)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        → rate.limiter: WARN
      </text>
      <text
        x="56"
        y="343"
        fill="rgba(239,68,68,0.48)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        → db.query: ERROR
      </text>
      <text
        x="56"
        y="354"
        fill="rgba(148,163,184,0.22)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        latency: 1842ms ↑
      </text>
    </svg>
  )
}

// ─── TEST canvas ──────────────────────────────────────────────────────────────

function TestCanvas({ visible }: { visible: boolean }) {
  return (
    <svg
      className="absolute inset-0 w-full h-full"
      viewBox="0 0 520 560"
      fill="none"
      preserveAspectRatio="xMidYMid slice"
      style={{
        opacity: visible ? 1 : 0,
        transition: "opacity 420ms ease-in-out",
        pointerEvents: "none",
      }}
    >
      <defs>
        <pattern
          id="grid-t"
          x="0"
          y="0"
          width="28"
          height="28"
          patternUnits="userSpaceOnUse"
        >
          <circle cx="1" cy="1" r="0.8" fill="rgba(255,255,255,0.06)" />
        </pattern>
        <radialGradient id="blob-green-t" cx="44%" cy="46%" r="54%">
          <stop offset="0%" stopColor="#10B981" stopOpacity="0.14" />
          <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="blob-blue-t" cx="66%" cy="62%" r="44%">
          <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.09" />
          <stop offset="100%" stopColor="#3B82F6" stopOpacity="0" />
        </radialGradient>
        <filter id="glow-t" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="2.5" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <rect width="520" height="560" fill="url(#grid-t)" />
      <ellipse cx="230" cy="285" rx="225" ry="200" fill="url(#blob-green-t)" />
      <ellipse cx="390" cy="360" rx="180" ry="162" fill="url(#blob-blue-t)" />

      {/* Spec label */}
      <text
        x="56"
        y="152"
        fill="rgba(148,163,184,0.2)"
        fontSize="8.5"
        fontFamily={MONO}
      >
        spec: openapi.yaml → 4 scenarios
      </text>

      {/* Execution flow line */}
      <line
        x1="68"
        y1="205"
        x2="468"
        y2="205"
        stroke="rgba(148,163,184,0.09)"
        strokeWidth="1"
        strokeDasharray="6 4"
      >
        <animate
          attributeName="stroke-dashoffset"
          from="40"
          to="0"
          dur="4.5s"
          repeatCount="indefinite"
        />
      </line>

      {/* Test card 1 — PASS */}
      <rect
        x="52"
        y="162"
        width="96"
        height="50"
        rx="6"
        fill="rgba(16,185,129,0.07)"
        stroke="rgba(16,185,129,0.2)"
        strokeWidth="0.75"
      />
      <text
        x="64"
        y="179"
        fill="rgba(16,185,129,0.5)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        TEST_001
      </text>
      <text
        x="64"
        y="191"
        fill="rgba(148,163,184,0.3)"
        fontSize="7"
        fontFamily={MONO}
      >
        GET /users
      </text>
      <circle cx="136" cy="200" r="6" fill="rgba(16,185,129,0.14)" />
      <path
        d="M133 200 L135.5 202.5 L139.5 197.5"
        stroke="rgba(16,185,129,0.72)"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Test card 2 — PASS */}
      <rect
        x="164"
        y="162"
        width="96"
        height="50"
        rx="6"
        fill="rgba(16,185,129,0.07)"
        stroke="rgba(16,185,129,0.2)"
        strokeWidth="0.75"
      />
      <text
        x="176"
        y="179"
        fill="rgba(16,185,129,0.5)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        TEST_002
      </text>
      <text
        x="176"
        y="191"
        fill="rgba(148,163,184,0.3)"
        fontSize="7"
        fontFamily={MONO}
      >
        POST /orders
      </text>
      <circle cx="248" cy="200" r="6" fill="rgba(16,185,129,0.14)" />
      <path
        d="M245 200 L247.5 202.5 L251.5 197.5"
        stroke="rgba(16,185,129,0.72)"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Test card 3 — RUNNING */}
      <rect
        x="276"
        y="162"
        width="96"
        height="50"
        rx="6"
        fill="rgba(59,130,246,0.06)"
        stroke="rgba(59,130,246,0.22)"
        strokeWidth="0.75"
      >
        <animate
          attributeName="stroke-opacity"
          values="0.22;0.44;0.22"
          dur="1.6s"
          repeatCount="indefinite"
        />
      </rect>
      <text
        x="288"
        y="179"
        fill="rgba(99,160,255,0.5)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        TEST_003
      </text>
      <text
        x="288"
        y="191"
        fill="rgba(148,163,184,0.3)"
        fontSize="7"
        fontFamily={MONO}
      >
        PUT /profile
      </text>
      <circle cx="360" cy="200" r="6" fill="rgba(59,130,246,0.1)" />
      <circle cx="360" cy="200" r="3" fill="rgba(99,160,255,0.52)">
        <animate
          attributeName="opacity"
          values="0.52;1;0.52"
          dur="1.6s"
          repeatCount="indefinite"
        />
      </circle>

      {/* Test card 4 — PASS */}
      <rect
        x="388"
        y="162"
        width="96"
        height="50"
        rx="6"
        fill="rgba(16,185,129,0.05)"
        stroke="rgba(16,185,129,0.16)"
        strokeWidth="0.75"
      />
      <text
        x="400"
        y="179"
        fill="rgba(16,185,129,0.42)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        TEST_004
      </text>
      <text
        x="400"
        y="191"
        fill="rgba(148,163,184,0.25)"
        fontSize="7"
        fontFamily={MONO}
      >
        DELETE /item
      </text>
      <circle cx="472" cy="200" r="6" fill="rgba(16,185,129,0.1)" />
      <path
        d="M469 200 L471.5 202.5 L475.5 197.5"
        stroke="rgba(16,185,129,0.56)"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Vertical connectors to result badges */}
      <line
        x1="100"
        y1="212"
        x2="100"
        y2="282"
        stroke="rgba(16,185,129,0.11)"
        strokeWidth="0.75"
      />
      <line
        x1="212"
        y1="212"
        x2="212"
        y2="300"
        stroke="rgba(16,185,129,0.11)"
        strokeWidth="0.75"
      />
      <line
        x1="324"
        y1="212"
        x2="324"
        y2="322"
        stroke="rgba(99,160,255,0.1)"
        strokeWidth="0.75"
      />
      <line
        x1="436"
        y1="212"
        x2="436"
        y2="290"
        stroke="rgba(16,185,129,0.09)"
        strokeWidth="0.75"
      />

      {/* Result badges */}
      <rect
        x="68"
        y="282"
        width="64"
        height="18"
        rx="9"
        fill="rgba(16,185,129,0.09)"
        stroke="rgba(16,185,129,0.22)"
        strokeWidth="0.75"
      />
      <text
        x="100"
        y="294"
        fill="rgba(16,185,129,0.58)"
        fontSize="8"
        fontFamily={MONO}
        textAnchor="middle"
      >
        200 OK
      </text>

      <rect
        x="180"
        y="300"
        width="64"
        height="18"
        rx="9"
        fill="rgba(16,185,129,0.09)"
        stroke="rgba(16,185,129,0.22)"
        strokeWidth="0.75"
      />
      <text
        x="212"
        y="312"
        fill="rgba(16,185,129,0.58)"
        fontSize="8"
        fontFamily={MONO}
        textAnchor="middle"
      >
        201 OK
      </text>

      <rect
        x="292"
        y="322"
        width="64"
        height="18"
        rx="9"
        fill="rgba(59,130,246,0.07)"
        stroke="rgba(59,130,246,0.22)"
        strokeWidth="0.75"
      >
        <animate
          attributeName="stroke-opacity"
          values="0.22;0.44;0.22"
          dur="1.6s"
          repeatCount="indefinite"
        />
      </rect>
      <text
        x="324"
        y="334"
        fill="rgba(99,160,255,0.5)"
        fontSize="8"
        fontFamily={MONO}
        textAnchor="middle"
      >
        running…
      </text>

      <rect
        x="404"
        y="290"
        width="64"
        height="18"
        rx="9"
        fill="rgba(16,185,129,0.09)"
        stroke="rgba(16,185,129,0.2)"
        strokeWidth="0.75"
      />
      <text
        x="436"
        y="302"
        fill="rgba(16,185,129,0.52)"
        fontSize="8"
        fontFamily={MONO}
        textAnchor="middle"
      >
        204 OK
      </text>

      {/* Summary panel */}
      <rect
        x="44"
        y="360"
        width="146"
        height="76"
        rx="6"
        fill="rgba(255,255,255,0.025)"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="0.75"
      />
      <text
        x="56"
        y="378"
        fill="rgba(148,163,184,0.34)"
        fontSize="8"
        fontFamily={MONO}
      >
        TEST SUMMARY
      </text>
      <line
        x1="56"
        y1="385"
        x2="181"
        y2="385"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="0.5"
      />
      <text
        x="56"
        y="399"
        fill="rgba(52,211,153,0.46)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        ✓ passed: 3
      </text>
      <text
        x="56"
        y="411"
        fill="rgba(99,160,255,0.4)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        ◌ running: 1
      </text>
      <text
        x="56"
        y="423"
        fill="rgba(148,163,184,0.24)"
        fontSize="7.5"
        fontFamily={MONO}
      >
        coverage: 84%
      </text>

      {/* Validation links */}
      <line
        x1="324"
        y1="358"
        x2="385"
        y2="390"
        stroke="rgba(16,185,129,0.09)"
        strokeWidth="0.75"
      />
      <line
        x1="385"
        y1="390"
        x2="462"
        y2="374"
        stroke="rgba(16,185,129,0.07)"
        strokeWidth="0.75"
      />
      <circle cx="385" cy="390" r="3" fill="rgba(16,185,129,0.28)" />
      <circle cx="462" cy="374" r="2.5" fill="rgba(16,185,129,0.22)" />
    </svg>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function App() {
  const [authState, setAuthState] = useState<AuthState>("idle")
  const [activeTab, setActiveTab] = useState<TabId>(0)

  const handleGoogleSignIn = async () => {
  setAuthState("loading")

  const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin,
      },
    })

    if (error) {
      console.error("Google sign-in failed:", error)
      setAuthState("error")
    }
  }

  return (
    <div
      className="fixed inset-0 flex items-center justify-center p-4 md:p-6"
      style={{
        boxSizing: "border-box",
        background: "#EFEFEF",
        fontFamily: FONT,
      }}
    >
      {/* ── Outer glass container ── */}
      <div
        className="relative w-full flex overflow-hidden"
        style={{
          maxWidth: "960px",
          minHeight: "580px",
          borderRadius: "24px",
          background: "rgba(255,255,255,0.52)",
          border: "1px solid rgba(255,255,255,0.72)",
          boxShadow:
            "0 2px 2px rgba(0,0,0,0.03), 0 8px 32px rgba(0,0,0,0.07), 0 24px 64px rgba(0,0,0,0.05)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
        }}
      >
        {/* Back to website pill */}
        <div className="absolute top-5 right-5 z-20">
          <a
            href="#"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "5px",
              padding: "6px 14px",
              borderRadius: "999px",
              background: "rgba(255,255,255,0.55)",
              border: "1px solid rgba(0,0,0,0.09)",
              color: "#888",
              fontFamily: FONT,
              fontSize: "12px",
              fontWeight: 400,
              textDecoration: "none",
              backdropFilter: "blur(8px)",
              WebkitBackdropFilter: "blur(8px)",
              transition: "color 200ms, background 200ms",
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLAnchorElement
              el.style.color = "#444"
              el.style.background = "rgba(255,255,255,0.8)"
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLAnchorElement
              el.style.color = "#888"
              el.style.background = "rgba(255,255,255,0.55)"
            }}
          >
            Back to website <span style={{ fontSize: "13px" }}>→</span>
          </a>
        </div>

        {/* ══ LEFT: Dark visual panel ══ */}
        <div
          className="relative hidden md:flex flex-col justify-between overflow-hidden flex-shrink-0"
          style={{
            width: "48%",
            background: "#0E1117",
            borderRadius: "18px",
            margin: "5px",
            padding: "32px",
          }}
        >
          {/* Canvas layers — all rendered, crossfaded via opacity */}
          <ExploreCanvas visible={activeTab === 0} />
          <DebugCanvas visible={activeTab === 1} />
          <TestCanvas visible={activeTab === 2} />

          {/* ── APICE branding ── */}
          <div
            className="relative z-10 select-none"
            style={{
              width: "fit-content",
            }}
          >
            <div
              style={{
                fontFamily: FONT,
                fontSize: "34px",
                fontWeight: 700,
                color: "#ffffff",
                letterSpacing: "-1.2px",
                lineHeight: 1,
                whiteSpace: "nowrap",
              }}
            >
              APICE.
            </div>

            <div
              style={{
                width: "100%",
                fontFamily: FONT,
                fontSize: "10px",
                fontWeight: 400,
                color: "rgba(255, 255, 255, 0.55)",
                textAlign: "right",
                marginTop: "5px",
                letterSpacing: "0.015em",
                lineHeight: 1,
                whiteSpace: "nowrap",
              }}
            >
              by Creviro.io
            </div>
          </div>

          {/* ── Bottom: crossfading headline + subtext + indicators ── */}
          <div className="relative z-10">
            {/* Text layers — stacked, crossfaded */}
            <div
              style={{
                position: "relative",
                height: "88px",
                marginBottom: "20px",
              }}
            >
              {TABS.map((tab, i) => (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    opacity: activeTab === i ? 1 : 0,
                    transition: "opacity 420ms ease-in-out",
                    pointerEvents: activeTab === i ? "auto" : "none",
                  }}
                >
                  <p
                    style={{
                      fontFamily: FONT,
                      fontSize: "20px",
                      fontWeight: 600,
                      color: "rgba(255,255,255,0.88)",
                      lineHeight: 1.28,
                      letterSpacing: "-0.35px",
                      margin: 0,
                    }}
                  >
                    {tab.headline}
                  </p>
                  <p
                    style={{
                      fontFamily: FONT,
                      fontSize: "12px",
                      fontWeight: 400,
                      color: "rgba(255,255,255,0.32)",
                      marginTop: "8px",
                      lineHeight: 1.55,
                    }}
                  >
                    {tab.sub}
                  </p>
                </div>
              ))}
            </div>

            {/* Indicator bars */}
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              {([0, 1, 2] as TabId[]).map((i) => (
                <button
                  key={i}
                  onClick={() => setActiveTab(i)}
                  aria-label={["Explore", "Debug", "Test"][i]}
                  style={{
                    height: "3px",
                    width: activeTab === i ? "48px" : "20px",
                    borderRadius: "999px",
                    background: "rgba(255,255,255,1)",
                    opacity: activeTab === i ? 1 : 0.28,
                    border: "none",
                    padding: 0,
                    cursor: "pointer",
                    transition:
                      "width 400ms ease-in-out, opacity 400ms ease-in-out",
                  }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* ══ RIGHT: Login panel ══ */}
        <div
          className="flex flex-col justify-center flex-1 px-8 md:px-12 py-14"
          style={{ minWidth: 0 }}
        >
          <div className="w-full mx-auto" style={{ maxWidth: "320px" }}>
            {/* Mobile brand */}
            <div className="md:hidden text-center mb-8">
              <div
                style={{
                  fontFamily: FONT,
                  fontSize: "26px",
                  fontWeight: 700,
                  color: "#1A1A1A",
                  letterSpacing: "-0.6px",
                }}
              >
                APICE.
              </div>
              <div
                style={{ fontSize: "11px", color: "#888", marginTop: "3px" }}
              >
                by Creviro.io
              </div>
            </div>

            {/* Heading */}
            <h1
              style={{
                fontFamily: FONT,
                fontSize: "25px",
                fontWeight: 600,
                color: "#1A1A1A",
                letterSpacing: "-0.45px",
                lineHeight: 1.2,
                margin: 0,
              }}
            >
              Sign in to APICE
            </h1>
            <p
              style={{
                fontFamily: FONT,
                fontSize: "13.5px",
                fontWeight: 400,
                color: "#848484",
                marginTop: "6px",
                marginBottom: "30px",
                lineHeight: 1.5,
              }}
            >
              Continue with your Google account to access your API workspace.
            </p>

            {/* Google button */}
            <button
              onClick={handleGoogleSignIn}
              disabled={authState === "loading"}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "10px",
                height: "46px",
                borderRadius: "12px",
                background:
                  authState === "loading"
                    ? "rgba(255,255,255,0.65)"
                    : "rgba(255,255,255,0.92)",
                border: "1px solid rgba(0,0,0,0.1)",
                color: "#1A1A1A",
                fontFamily: FONT,
                fontSize: "14px",
                fontWeight: 500,
                cursor: authState === "loading" ? "not-allowed" : "pointer",
                boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                transition:
                  "background 200ms, box-shadow 200ms, border-color 200ms",
              }}
              onMouseEnter={(e) => {
                if (authState !== "loading") {
                  const el = e.currentTarget as HTMLButtonElement
                  el.style.background = "rgba(255,255,255,1)"
                  el.style.boxShadow = "0 2px 12px rgba(0,0,0,0.1)"
                  el.style.borderColor = "rgba(0,0,0,0.14)"
                }
              }}
              onMouseLeave={(e) => {
                const el = e.currentTarget as HTMLButtonElement
                el.style.background =
                  authState === "loading"
                    ? "rgba(255,255,255,0.65)"
                    : "rgba(255,255,255,0.92)"
                el.style.boxShadow = "0 1px 3px rgba(0,0,0,0.06)"
                el.style.borderColor = "rgba(0,0,0,0.1)"
              }}
            >
              {authState === "loading" ? (
                <>
                  <svg
                    className="animate-spin"
                    width="17"
                    height="17"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="rgba(0,0,0,0.08)"
                      strokeWidth="3"
                    />
                    <path
                      d="M12 2a10 10 0 0 1 10 10"
                      stroke="#555"
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                  </svg>
                  <span style={{ color: "#888" }}>Signing you in…</span>
                </>
              ) : (
                <>
                  <GoogleGlyph />
                  Continue with Google
                </>
              )}
            </button>

            {/* Error message */}
            {authState === "error" && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  marginTop: "10px",
                  padding: "9px 12px",
                  borderRadius: "9px",
                  background: "rgba(239,68,68,0.05)",
                  border: "1px solid rgba(239,68,68,0.14)",
                }}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  style={{ flexShrink: 0 }}
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="rgba(220,38,38,0.62)"
                    strokeWidth="1.5"
                  />
                  <line
                    x1="12"
                    y1="8"
                    x2="12"
                    y2="13.5"
                    stroke="rgba(220,38,38,0.62)"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                  <circle
                    cx="12"
                    cy="16.5"
                    r="0.9"
                    fill="rgba(220,38,38,0.62)"
                  />
                </svg>
                <span
                  style={{
                    fontFamily: FONT,
                    fontSize: "12.5px",
                    color: "rgba(185,28,28,0.82)",
                    lineHeight: 1.4,
                  }}
                >
                  Authentication failed. Please try again.
                </span>
              </div>
            )}

            {/* Divider */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                margin: "22px 0",
              }}
            >
              <div
                style={{
                  flex: 1,
                  height: "1px",
                  background: "rgba(0,0,0,0.08)",
                }}
              />
              <span
                style={{
                  fontFamily: FONT,
                  fontSize: "11px",
                  color: "#B0B0B0",
                  letterSpacing: "0.05em",
                }}
              >
                or
              </span>
              <div
                style={{
                  flex: 1,
                  height: "1px",
                  background: "rgba(0,0,0,0.08)",
                }}
              />
            </div>

            {/* Email option */}
            <button
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: "42px",
                borderRadius: "12px",
                background: "transparent",
                border: "1px solid rgba(0,0,0,0.09)",
                color: "#848484",
                fontFamily: FONT,
                fontSize: "13.5px",
                fontWeight: 400,
                cursor: "pointer",
                transition: "background 200ms, color 200ms",
              }}
              onMouseEnter={(e) => {
                const el = e.currentTarget as HTMLButtonElement
                el.style.background = "rgba(0,0,0,0.025)"
                el.style.color = "#444"
              }}
              onMouseLeave={(e) => {
                const el = e.currentTarget as HTMLButtonElement
                el.style.background = "transparent"
                el.style.color = "#848484"
              }}
            >
              Continue with email
            </button>

            {/* Legal */}
            <p
              style={{
                fontFamily: FONT,
                fontSize: "11px",
                color: "#B0B0B0",
                textAlign: "center",
                marginTop: "26px",
                lineHeight: 1.65,
              }}
            >
              By signing in, you agree to our{" "}
              <a
                href="#"
                style={{ color: "#888", textDecoration: "underline" }}
              >
                Terms
              </a>{" "}
              and{" "}
              <a
                href="#"
                style={{ color: "#888", textDecoration: "underline" }}
              >
                Privacy Policy
              </a>
              .
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
