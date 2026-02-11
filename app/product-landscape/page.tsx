"use client"

import { useState, useMemo } from "react"

// ────────────────────────────────────────────────────────────
// Types
// ────────────────────────────────────────────────────────────

const FUNCTION_GROUPS = [
  "Marketing",
  "Sales",
  "Engineering",
  "Customer Success",
  "Finance",
  "HR & People",
  "Operations",
  "Data & Analytics",
  "Security",
  "IT Infrastructure",
  "Legal & Compliance",
  "Product",
] as const
type FunctionGroup = (typeof FUNCTION_GROUPS)[number]

const PRODUCT_TYPES = ["Platform", "Tool", "Service", "Integration"] as const
type ProductType = (typeof PRODUCT_TYPES)[number]

const FAMILY_LINES = [
  "Enterprise Suite",
  "Growth Cloud",
  "Analytics Hub",
  "Commerce Engine",
  "Workflow Studio",
  "Connect Platform",
  "Identity Shield",
  "DevOps Pipeline",
  "Insights Lab",
  "Talent Cloud",
  "Revenue Ops",
  "Compliance Center",
] as const
type FamilyLine = (typeof FAMILY_LINES)[number]

interface Product {
  name: string
  functionGroup: FunctionGroup
  productType: ProductType
  familyLine: FamilyLine
}

// ────────────────────────────────────────────────────────────
// Color system — each function group gets a light bg + dark text + accent dot
// ────────────────────────────────────────────────────────────

const FUNCTION_COLORS: Record<
  FunctionGroup,
  { bg: string; text: string; dot: string }
> = {
  Marketing: { bg: "#DBEAFE", text: "#1E40AF", dot: "#3B82F6" },
  Sales: { bg: "#D1FAE5", text: "#065F46", dot: "#10B981" },
  Engineering: { bg: "#E0E7FF", text: "#3730A3", dot: "#6366F1" },
  "Customer Success": { bg: "#FEF3C7", text: "#92400E", dot: "#F59E0B" },
  Finance: { bg: "#FEE2E2", text: "#991B1B", dot: "#EF4444" },
  "HR & People": { bg: "#FCE7F3", text: "#9D174D", dot: "#EC4899" },
  Operations: { bg: "#EDE9FE", text: "#5B21B6", dot: "#8B5CF6" },
  "Data & Analytics": { bg: "#CFFAFE", text: "#155E75", dot: "#06B6D4" },
  Security: { bg: "#FFEDD5", text: "#9A3412", dot: "#F97316" },
  "IT Infrastructure": { bg: "#F1F5F9", text: "#334155", dot: "#64748B" },
  "Legal & Compliance": { bg: "#ECFCCB", text: "#3F6212", dot: "#84CC16" },
  Product: { bg: "#CCFBF1", text: "#115E59", dot: "#14B8A6" },
}

// ────────────────────────────────────────────────────────────
// Product data — 95 products distributed across 3 dimensions
// ────────────────────────────────────────────────────────────

const PRODUCTS: Product[] = [
  // ── Enterprise Suite (10) ─────────────────────────────────
  { name: "Command Center", functionGroup: "Operations", productType: "Platform", familyLine: "Enterprise Suite" },
  { name: "Enterprise Analytics", functionGroup: "Data & Analytics", productType: "Platform", familyLine: "Enterprise Suite" },
  { name: "SSO Gateway", functionGroup: "Security", productType: "Integration", familyLine: "Enterprise Suite" },
  { name: "Billing Suite", functionGroup: "Finance", productType: "Tool", familyLine: "Enterprise Suite" },
  { name: "CRM Pro", functionGroup: "Sales", productType: "Platform", familyLine: "Enterprise Suite" },
  { name: "Support Hub", functionGroup: "Customer Success", productType: "Service", familyLine: "Enterprise Suite" },
  { name: "Compliance Mgr", functionGroup: "Legal & Compliance", productType: "Tool", familyLine: "Enterprise Suite" },
  { name: "API Gateway", functionGroup: "Engineering", productType: "Integration", familyLine: "Enterprise Suite" },
  { name: "HR Portal", functionGroup: "HR & People", productType: "Platform", familyLine: "Enterprise Suite" },
  { name: "Marketing Hub", functionGroup: "Marketing", productType: "Platform", familyLine: "Enterprise Suite" },

  // ── Growth Cloud (8) ──────────────────────────────────────
  { name: "Attribution Pro", functionGroup: "Marketing", productType: "Tool", familyLine: "Growth Cloud" },
  { name: "Experiments", functionGroup: "Product", productType: "Tool", familyLine: "Growth Cloud" },
  { name: "Engage Cloud", functionGroup: "Marketing", productType: "Platform", familyLine: "Growth Cloud" },
  { name: "Lead Signals", functionGroup: "Sales", productType: "Service", familyLine: "Growth Cloud" },
  { name: "Onboard Flow", functionGroup: "Customer Success", productType: "Service", familyLine: "Growth Cloud" },
  { name: "Campaigns", functionGroup: "Marketing", productType: "Tool", familyLine: "Growth Cloud" },
  { name: "Referral Engine", functionGroup: "Marketing", productType: "Integration", familyLine: "Growth Cloud" },
  { name: "Forecaster", functionGroup: "Data & Analytics", productType: "Tool", familyLine: "Growth Cloud" },

  // ── Analytics Hub (9) ─────────────────────────────────────
  { name: "Live Dashboards", functionGroup: "Data & Analytics", productType: "Platform", familyLine: "Analytics Hub" },
  { name: "Predict AI", functionGroup: "Data & Analytics", productType: "Service", familyLine: "Analytics Hub" },
  { name: "Warehouse Sync", functionGroup: "Engineering", productType: "Integration", familyLine: "Analytics Hub" },
  { name: "Report Builder", functionGroup: "Data & Analytics", productType: "Tool", familyLine: "Analytics Hub" },
  { name: "User Analytics", functionGroup: "Product", productType: "Tool", familyLine: "Analytics Hub" },
  { name: "Revenue Intel", functionGroup: "Finance", productType: "Tool", familyLine: "Analytics Hub" },
  { name: "Mix Modeler", functionGroup: "Marketing", productType: "Tool", familyLine: "Analytics Hub" },
  { name: "Funnel Tracker", functionGroup: "Sales", productType: "Tool", familyLine: "Analytics Hub" },
  { name: "Ops Metrics", functionGroup: "Operations", productType: "Service", familyLine: "Analytics Hub" },

  // ── Commerce Engine (8) ───────────────────────────────────
  { name: "Storefront", functionGroup: "Product", productType: "Platform", familyLine: "Commerce Engine" },
  { name: "Pay Process", functionGroup: "Finance", productType: "Service", familyLine: "Commerce Engine" },
  { name: "Inventory Mgr", functionGroup: "Operations", productType: "Tool", familyLine: "Commerce Engine" },
  { name: "Fulfillment", functionGroup: "Operations", productType: "Service", familyLine: "Commerce Engine" },
  { name: "Catalog Pro", functionGroup: "Product", productType: "Tool", familyLine: "Commerce Engine" },
  { name: "Price Engine", functionGroup: "Sales", productType: "Service", familyLine: "Commerce Engine" },
  { name: "Checkout Pro", functionGroup: "Product", productType: "Tool", familyLine: "Commerce Engine" },
  { name: "Commerce API", functionGroup: "Engineering", productType: "Integration", familyLine: "Commerce Engine" },

  // ── Workflow Studio (8) ───────────────────────────────────
  { name: "Automator", functionGroup: "Operations", productType: "Platform", familyLine: "Workflow Studio" },
  { name: "Approvals", functionGroup: "Operations", productType: "Tool", familyLine: "Workflow Studio" },
  { name: "Orchestrator", functionGroup: "Engineering", productType: "Service", familyLine: "Workflow Studio" },
  { name: "Doc Flows", functionGroup: "Legal & Compliance", productType: "Tool", familyLine: "Workflow Studio" },
  { name: "HR Flows", functionGroup: "HR & People", productType: "Service", familyLine: "Workflow Studio" },
  { name: "Sales Flows", functionGroup: "Sales", productType: "Tool", familyLine: "Workflow Studio" },
  { name: "Mktg Automator", functionGroup: "Marketing", productType: "Integration", familyLine: "Workflow Studio" },
  { name: "Service Desk", functionGroup: "IT Infrastructure", productType: "Service", familyLine: "Workflow Studio" },

  // ── Connect Platform (9) ──────────────────────────────────
  { name: "Unified Inbox", functionGroup: "Customer Success", productType: "Platform", familyLine: "Connect Platform" },
  { name: "Chat Widget", functionGroup: "Customer Success", productType: "Tool", familyLine: "Connect Platform" },
  { name: "Video Meet", functionGroup: "Operations", productType: "Service", familyLine: "Connect Platform" },
  { name: "SMS Connect", functionGroup: "Marketing", productType: "Integration", familyLine: "Connect Platform" },
  { name: "Email Delivery", functionGroup: "Marketing", productType: "Service", familyLine: "Connect Platform" },
  { name: "Voice Cloud", functionGroup: "Customer Success", productType: "Platform", familyLine: "Connect Platform" },
  { name: "Webhooks", functionGroup: "Engineering", productType: "Tool", familyLine: "Connect Platform" },
  { name: "Partner Portal", functionGroup: "Sales", productType: "Platform", familyLine: "Connect Platform" },
  { name: "Team Collab", functionGroup: "HR & People", productType: "Tool", familyLine: "Connect Platform" },

  // ── Identity Shield (7) ───────────────────────────────────
  { name: "Multi-Factor", functionGroup: "Security", productType: "Service", familyLine: "Identity Shield" },
  { name: "ID Provider", functionGroup: "Security", productType: "Platform", familyLine: "Identity Shield" },
  { name: "Access Ctrl", functionGroup: "Security", productType: "Tool", familyLine: "Identity Shield" },
  { name: "Dir Sync", functionGroup: "IT Infrastructure", productType: "Integration", familyLine: "Identity Shield" },
  { name: "Session Mgr", functionGroup: "Security", productType: "Service", familyLine: "Identity Shield" },
  { name: "Audit Tool", functionGroup: "Legal & Compliance", productType: "Tool", familyLine: "Identity Shield" },
  { name: "Threat Detect", functionGroup: "Security", productType: "Service", familyLine: "Identity Shield" },

  // ── DevOps Pipeline (8) ───────────────────────────────────
  { name: "CI/CD Runner", functionGroup: "Engineering", productType: "Platform", familyLine: "DevOps Pipeline" },
  { name: "Container Reg", functionGroup: "Engineering", productType: "Service", familyLine: "DevOps Pipeline" },
  { name: "Deploy Mgr", functionGroup: "Engineering", productType: "Tool", familyLine: "DevOps Pipeline" },
  { name: "Infra Monitor", functionGroup: "IT Infrastructure", productType: "Service", familyLine: "DevOps Pipeline" },
  { name: "Log Aggregator", functionGroup: "IT Infrastructure", productType: "Tool", familyLine: "DevOps Pipeline" },
  { name: "Feature Flags", functionGroup: "Product", productType: "Tool", familyLine: "DevOps Pipeline" },
  { name: "API Docs", functionGroup: "Engineering", productType: "Tool", familyLine: "DevOps Pipeline" },
  { name: "Code Review", functionGroup: "Engineering", productType: "Integration", familyLine: "DevOps Pipeline" },

  // ── Insights Lab (7) ──────────────────────────────────────
  { name: "A/B Engine", functionGroup: "Product", productType: "Platform", familyLine: "Insights Lab" },
  { name: "Survey Builder", functionGroup: "Customer Success", productType: "Tool", familyLine: "Insights Lab" },
  { name: "NPS Tracker", functionGroup: "Customer Success", productType: "Service", familyLine: "Insights Lab" },
  { name: "Mkt Research", functionGroup: "Marketing", productType: "Service", familyLine: "Insights Lab" },
  { name: "Sentiment AI", functionGroup: "Data & Analytics", productType: "Tool", familyLine: "Insights Lab" },
  { name: "Compete Intel", functionGroup: "Sales", productType: "Service", familyLine: "Insights Lab" },
  { name: "Customer 360", functionGroup: "Data & Analytics", productType: "Platform", familyLine: "Insights Lab" },

  // ── Talent Cloud (7) ──────────────────────────────────────
  { name: "Applicant ATS", functionGroup: "HR & People", productType: "Platform", familyLine: "Talent Cloud" },
  { name: "Reviews Pro", functionGroup: "HR & People", productType: "Tool", familyLine: "Talent Cloud" },
  { name: "Learning LMS", functionGroup: "HR & People", productType: "Platform", familyLine: "Talent Cloud" },
  { name: "Comp Planner", functionGroup: "Finance", productType: "Tool", familyLine: "Talent Cloud" },
  { name: "Pulse Survey", functionGroup: "HR & People", productType: "Service", familyLine: "Talent Cloud" },
  { name: "Org Chart", functionGroup: "HR & People", productType: "Tool", familyLine: "Talent Cloud" },
  { name: "Benefits Hub", functionGroup: "HR & People", productType: "Service", familyLine: "Talent Cloud" },

  // ── Revenue Ops (7) ───────────────────────────────────────
  { name: "Pipeline Mgr", functionGroup: "Sales", productType: "Platform", familyLine: "Revenue Ops" },
  { name: "Quote Gen", functionGroup: "Sales", productType: "Tool", familyLine: "Revenue Ops" },
  { name: "Contract Mgr", functionGroup: "Legal & Compliance", productType: "Tool", familyLine: "Revenue Ops" },
  { name: "Rev Recognition", functionGroup: "Finance", productType: "Service", familyLine: "Revenue Ops" },
  { name: "Commission Trk", functionGroup: "Finance", productType: "Tool", familyLine: "Revenue Ops" },
  { name: "Deal Room", functionGroup: "Sales", productType: "Platform", familyLine: "Revenue Ops" },
  { name: "Subscriptions", functionGroup: "Finance", productType: "Service", familyLine: "Revenue Ops" },

  // ── Compliance Center (7) ─────────────────────────────────
  { name: "Policy Mgr", functionGroup: "Legal & Compliance", productType: "Platform", familyLine: "Compliance Center" },
  { name: "Audit Trail", functionGroup: "Legal & Compliance", productType: "Service", familyLine: "Compliance Center" },
  { name: "Privacy Tool", functionGroup: "Legal & Compliance", productType: "Tool", familyLine: "Compliance Center" },
  { name: "Reg Reporting", functionGroup: "Finance", productType: "Service", familyLine: "Compliance Center" },
  { name: "Risk Assess", functionGroup: "Security", productType: "Tool", familyLine: "Compliance Center" },
  { name: "Vendor Mgr", functionGroup: "Operations", productType: "Tool", familyLine: "Compliance Center" },
  { name: "GDPR Toolkit", functionGroup: "Legal & Compliance", productType: "Integration", familyLine: "Compliance Center" },
]

// ────────────────────────────────────────────────────────────
// Helper components
// ────────────────────────────────────────────────────────────

function TypeShape({ type }: { type: ProductType }) {
  switch (type) {
    case "Platform":
      return (
        <div className="mx-auto mb-2">
          <div className="w-8 h-8 rounded-lg bg-slate-800 mx-auto" />
        </div>
      )
    case "Tool":
      return (
        <div className="mx-auto mb-2 flex items-center justify-center w-8 h-8">
          <div className="w-5 h-5 rounded-sm bg-slate-800 rotate-45" />
        </div>
      )
    case "Service":
      return (
        <div className="mx-auto mb-2">
          <div className="w-8 h-8 rounded-full bg-slate-800 mx-auto" />
        </div>
      )
    case "Integration":
      return (
        <div className="mx-auto mb-2 relative w-10 h-8 flex items-center justify-center">
          <div className="absolute left-0 w-6 h-6 rounded-full border-[2.5px] border-slate-800 bg-white" />
          <div className="absolute right-0 w-6 h-6 rounded-full border-[2.5px] border-slate-800 bg-white" />
        </div>
      )
  }
}

function DistributionBar({
  label,
  count,
  max,
  color,
}: {
  label: string
  count: number
  max: number
  color: string
}) {
  return (
    <div className="flex items-center gap-2 group/bar">
      <span className="text-[11px] text-slate-500 w-[120px] truncate text-right flex-shrink-0 group-hover/bar:text-slate-700 transition-colors">
        {label}
      </span>
      <div className="flex-1 h-4 bg-slate-100 rounded-sm overflow-hidden">
        <div
          className="h-full rounded-sm transition-all duration-500 group-hover/bar:brightness-110"
          style={{
            width: `${(count / max) * 100}%`,
            backgroundColor: color,
          }}
        />
      </div>
      <span className="text-[11px] font-medium text-slate-600 w-5 text-right flex-shrink-0 group-hover/bar:text-slate-900 transition-colors">
        {count}
      </span>
    </div>
  )
}

// ────────────────────────────────────────────────────────────
// Main page component
// ────────────────────────────────────────────────────────────

export default function ProductLandscapePage() {
  const [activeGroup, setActiveGroup] = useState<FunctionGroup | null>(null)

  const getProducts = (family: FamilyLine, type: ProductType) =>
    PRODUCTS.filter(
      (p) => p.familyLine === family && p.productType === type
    )

  // Distribution stats
  const functionCounts = useMemo(() => {
    return FUNCTION_GROUPS.map((g) => ({
      name: g,
      count: PRODUCTS.filter((p) => p.functionGroup === g).length,
    }))
  }, [])

  const typeCounts = useMemo(() => {
    return PRODUCT_TYPES.map((t) => ({
      name: t,
      count: PRODUCTS.filter((p) => p.productType === t).length,
    }))
  }, [])

  const familyCounts = useMemo(() => {
    return FAMILY_LINES.map((f) => ({
      name: f,
      count: PRODUCTS.filter((p) => p.familyLine === f).length,
    }))
  }, [])

  const maxFunctionCount = Math.max(...functionCounts.map((f) => f.count))
  const maxTypeCount = Math.max(...typeCounts.map((t) => t.count))
  const maxFamilyCount = Math.max(...familyCounts.map((f) => f.count))

  return (
    <main className="min-h-screen bg-white selection:bg-violet-100">
      {/* ── Top accent bar ─────────────────────────────────── */}
      <div className="h-1.5 bg-gradient-to-r from-blue-500 via-violet-500 to-emerald-500" />

      {/* ── Header ─────────────────────────────────────────── */}
      <header className="border-b border-slate-200">
        <div className="max-w-[1440px] mx-auto px-6 lg:px-10 py-10">
          <p className="text-[11px] font-semibold tracking-[0.15em] text-slate-400 uppercase mb-3">
            Organization Overview
          </p>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
            Product Landscape
          </h1>
          <p className="mt-2 text-slate-500 max-w-2xl text-[15px] leading-relaxed">
            How our 95 products align across function groups, product types,
            and family lines — a single view of the full portfolio.
          </p>

          {/* Stats row */}
          <div className="mt-8 flex flex-wrap gap-8">
            {[
              { value: "95", label: "Products" },
              { value: "12", label: "Family Lines" },
              { value: "4", label: "Product Types" },
              { value: "12", label: "Function Groups" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="flex items-center gap-3 border border-slate-200 rounded-lg px-5 py-3 hover:border-slate-300 hover:shadow-sm transition-all duration-200"
              >
                <span className="text-2xl font-bold text-slate-900">
                  {stat.value}
                </span>
                <span className="text-sm text-slate-500">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </header>

      {/* ── Legend: Function Groups (clickable filter) ──────── */}
      <section className="border-b border-slate-200 bg-slate-50/60">
        <div className="max-w-[1440px] mx-auto px-6 lg:px-10 py-5">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[11px] font-semibold tracking-[0.15em] text-slate-400 uppercase">
              Function Groups &mdash; click to filter
            </p>
            {activeGroup && (
              <button
                onClick={() => setActiveGroup(null)}
                className="text-xs text-slate-500 hover:text-slate-800 underline underline-offset-2 transition-colors"
              >
                Clear filter
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-x-5 gap-y-2.5">
            {FUNCTION_GROUPS.map((group) => {
              const colors = FUNCTION_COLORS[group]
              const isActive =
                activeGroup === null || activeGroup === group
              return (
                <button
                  key={group}
                  onClick={() =>
                    setActiveGroup(activeGroup === group ? null : group)
                  }
                  className={`flex items-center gap-2 text-[13px] rounded-full px-3 py-1.5 transition-all duration-200 hover:opacity-100 ${
                    activeGroup === group
                      ? "ring-1 ring-slate-300 bg-white shadow-sm opacity-100"
                      : isActive
                        ? "opacity-100 hover:bg-white/60"
                        : "opacity-25 hover:opacity-60"
                  }`}
                >
                  <span
                    className="w-3 h-3 rounded-[3px] flex-shrink-0 transition-transform duration-200"
                    style={{
                      backgroundColor: colors.dot,
                      transform: activeGroup === group ? "scale(1.2)" : "scale(1)",
                    }}
                  />
                  <span className="text-slate-700">{group}</span>
                </button>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── Shape key: Product Types ───────────────────────── */}
      <section className="border-b border-slate-100">
        <div className="max-w-[1440px] mx-auto px-6 lg:px-10 py-4">
          <div className="flex items-center gap-8">
            <p className="text-[11px] font-semibold tracking-[0.15em] text-slate-400 uppercase flex-shrink-0">
              Product Types
            </p>
            <div className="flex flex-wrap gap-6">
              {PRODUCT_TYPES.map((type) => (
                <div key={type} className="flex items-center gap-2">
                  {type === "Platform" && (
                    <div className="w-4 h-4 rounded-[3px] bg-slate-700" />
                  )}
                  {type === "Tool" && (
                    <div className="w-3 h-3 rounded-[2px] bg-slate-700 rotate-45" />
                  )}
                  {type === "Service" && (
                    <div className="w-4 h-4 rounded-full bg-slate-700" />
                  )}
                  {type === "Integration" && (
                    <div className="relative w-5 h-4 flex items-center">
                      <div className="absolute left-0 w-3.5 h-3.5 rounded-full border-2 border-slate-700 bg-white" />
                      <div className="absolute left-1.5 w-3.5 h-3.5 rounded-full border-2 border-slate-700 bg-white" />
                    </div>
                  )}
                  <span className="text-[13px] text-slate-600">{type}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Matrix Grid ────────────────────────────────────── */}
      <section className="max-w-[1440px] mx-auto px-6 lg:px-10 py-8">
        <div className="overflow-x-auto -mx-6 px-6 lg:-mx-10 lg:px-10">
          <div className="min-w-[920px]">
            {/* Column headers */}
            <div className="grid grid-cols-[180px_repeat(4,1fr)] gap-px bg-slate-200 rounded-t-xl overflow-hidden">
              {/* Top-left corner cell */}
              <div className="bg-white p-4 flex items-end">
                <span className="text-[11px] font-semibold tracking-[0.1em] text-slate-400 uppercase">
                  Family Line
                </span>
              </div>
              {/* Type column headers */}
              {PRODUCT_TYPES.map((type) => (
                <div key={type} className="bg-white p-4 text-center">
                  <TypeShape type={type} />
                  <p className="text-sm font-semibold text-slate-800">
                    {type}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {PRODUCTS.filter((p) => p.productType === type).length}{" "}
                    products
                  </p>
                </div>
              ))}
            </div>

            {/* Data rows */}
            {FAMILY_LINES.map((family, rowIndex) => {
              const familyTotal = PRODUCTS.filter(
                (p) => p.familyLine === family
              ).length
              const isEven = rowIndex % 2 === 0
              const rowBg = isEven ? "bg-white" : "bg-slate-50/50"

              return (
                <div
                  key={family}
                  className="grid grid-cols-[180px_repeat(4,1fr)] gap-px bg-slate-200 group/row"
                >
                  {/* Row label */}
                  <div className={`${rowBg} p-4 flex items-start group-hover/row:bg-slate-50`}>
                    <div>
                      <p className="text-[13px] font-semibold text-slate-800 leading-tight">
                        {family}
                      </p>
                      <p className="text-[11px] text-slate-400 mt-1">
                        {familyTotal} products
                      </p>
                    </div>
                  </div>

                  {/* Cells for each product type */}
                  {PRODUCT_TYPES.map((type) => {
                    const products = getProducts(family, type)
                    return (
                      <div
                        key={type}
                        className={`${rowBg} p-3 min-h-[72px] group-hover/row:bg-slate-50 transition-colors duration-150`}
                      >
                        <div className="flex flex-wrap gap-1.5">
                          {products.map((product) => {
                            const colors =
                              FUNCTION_COLORS[product.functionGroup]
                            const isActive =
                              activeGroup === null ||
                              activeGroup === product.functionGroup
                            return (
                              <span
                                key={product.name}
                                className={`inline-flex items-center px-2.5 py-[5px] rounded-md text-[11px] font-medium leading-none transition-all duration-200 cursor-default hover:scale-105 hover:shadow-md ${
                                  isActive
                                    ? "opacity-100 shadow-sm"
                                    : "opacity-[0.12] hover:opacity-30"
                                }`}
                                style={{
                                  backgroundColor: colors.bg,
                                  color: colors.text,
                                  border: `1px solid ${colors.dot}20`,
                                }}
                                title={`${product.name}\n${product.functionGroup} · ${product.productType}\n${product.familyLine}`}
                              >
                                <span
                                  className="w-1.5 h-1.5 rounded-full mr-1.5 flex-shrink-0"
                                  style={{ backgroundColor: colors.dot }}
                                />
                                {product.name}
                              </span>
                            )
                          })}
                          {products.length === 0 && (
                            <span className="text-slate-300 text-xs">
                              &mdash;
                            </span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )
            })}

            {/* Bottom border radius */}
            <div className="h-px bg-slate-200 rounded-b-xl" />
          </div>
        </div>
      </section>

      {/* ── Distribution Summary ───────────────────────────── */}
      <section className="border-t border-slate-200 bg-slate-50/60">
        <div className="max-w-[1440px] mx-auto px-6 lg:px-10 py-10">
          <p className="text-[11px] font-semibold tracking-[0.15em] text-slate-400 uppercase mb-6">
            Distribution Summary
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {/* By Function Group */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-4">
                By Function Group
              </h3>
              <div className="space-y-2">
                {functionCounts
                  .sort((a, b) => b.count - a.count)
                  .map((item) => (
                    <DistributionBar
                      key={item.name}
                      label={item.name}
                      count={item.count}
                      max={maxFunctionCount}
                      color={FUNCTION_COLORS[item.name as FunctionGroup].dot}
                    />
                  ))}
              </div>
            </div>

            {/* By Product Type */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-4">
                By Product Type
              </h3>
              <div className="space-y-2">
                {typeCounts
                  .sort((a, b) => b.count - a.count)
                  .map((item) => (
                    <DistributionBar
                      key={item.name}
                      label={item.name}
                      count={item.count}
                      max={maxTypeCount}
                      color="#475569"
                    />
                  ))}
              </div>

              {/* Type shape legend (mini) */}
              <div className="mt-6 pt-4 border-t border-slate-200">
                <p className="text-[11px] text-slate-400 uppercase tracking-wide mb-3">
                  Shape Key
                </p>
                <div className="grid grid-cols-2 gap-3">
                  {PRODUCT_TYPES.map((type) => (
                    <div
                      key={type}
                      className="flex items-center gap-2 text-[11px] text-slate-500"
                    >
                      {type === "Platform" && (
                        <div className="w-3 h-3 rounded-[2px] bg-slate-500" />
                      )}
                      {type === "Tool" && (
                        <div className="w-2.5 h-2.5 rounded-[1px] bg-slate-500 rotate-45" />
                      )}
                      {type === "Service" && (
                        <div className="w-3 h-3 rounded-full bg-slate-500" />
                      )}
                      {type === "Integration" && (
                        <div className="relative w-4 h-3">
                          <div className="absolute left-0 w-2.5 h-2.5 rounded-full border-[1.5px] border-slate-500 bg-white" />
                          <div className="absolute left-1 w-2.5 h-2.5 rounded-full border-[1.5px] border-slate-500 bg-white" />
                        </div>
                      )}
                      {type}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* By Family Line */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-4">
                By Family Line
              </h3>
              <div className="space-y-2">
                {familyCounts
                  .sort((a, b) => b.count - a.count)
                  .map((item) => (
                    <DistributionBar
                      key={item.name}
                      label={item.name}
                      count={item.count}
                      max={maxFamilyCount}
                      color="#818CF8"
                    />
                  ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────── */}
      <footer className="border-t border-slate-200">
        <div className="max-w-[1440px] mx-auto px-6 lg:px-10 py-6">
          <p className="text-xs text-slate-400">
            Product Landscape &middot; 95 Products &middot; 3 Classification
            Dimensions &middot; Shapes &amp; Text
          </p>
        </div>
      </footer>
    </main>
  )
}
