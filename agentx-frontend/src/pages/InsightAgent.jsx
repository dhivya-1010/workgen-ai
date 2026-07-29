import { useEffect, useMemo, useState } from "react";
import ResultCard from "../components/ResultCard";
import { getInsights } from "../services/api";

// ---------------------------------------------------------------------------
// Source icons and display config
// ---------------------------------------------------------------------------

const SOURCE_CONFIG = {
  Email: {
    icon: "✉️",
    label: "Email Intelligence",
    color: {
      dark: "bg-sky-500/15 text-sky-300 border-sky-400/30",
      light: "bg-sky-100 text-sky-700 border-sky-300",
    },
  },
  Meeting: {
    icon: "🧠",
    label: "Meeting Intelligence",
    color: {
      dark: "bg-violet-500/15 text-violet-300 border-violet-400/30",
      light: "bg-violet-100 text-violet-700 border-violet-300",
    },
  },
  Knowledge: {
    icon: "🗂️",
    label: "Org Knowledge",
    color: {
      dark: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
      light: "bg-emerald-100 text-emerald-700 border-emerald-300",
    },
  },
  Analytics: {
    icon: "📊",
    label: "Analytics",
    color: {
      dark: "bg-amber-500/15 text-amber-300 border-amber-400/30",
      light: "bg-amber-100 text-amber-700 border-amber-300",
    },
  },
};

const PRIORITY_CONFIG = {
  high: {
    label: "High",
    color: {
      dark: "bg-rose-500/15 text-rose-300 border-rose-400/30",
      light: "bg-rose-100 text-rose-700 border-rose-300",
    },
    dot: "bg-rose-400",
    dotLight: "bg-rose-500",
  },
  medium: {
    label: "Medium",
    color: {
      dark: "bg-amber-500/15 text-amber-300 border-amber-400/30",
      light: "bg-amber-100 text-amber-700 border-amber-300",
    },
    dot: "bg-amber-400",
    dotLight: "bg-amber-500",
  },
  low: {
    label: "Low",
    color: {
      dark: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
      light: "bg-emerald-100 text-emerald-700 border-emerald-300",
    },
    dot: "bg-emerald-400",
    dotLight: "bg-emerald-500",
  },
};

const SOURCES = ["All", "Email", "Meeting", "Knowledge", "Analytics"];
const PRIORITIES = ["All", "high", "medium", "low"];

// ---------------------------------------------------------------------------
// Helper: format ISO timestamp to readable relative time
// ---------------------------------------------------------------------------

function formatDetectedAt(isoString) {
  if (!isoString) return "";
  const now = new Date();
  const date = new Date(isoString);
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}

// ---------------------------------------------------------------------------
// Stat card for summary bar
// ---------------------------------------------------------------------------

function StatCard({ icon, label, value, dark }) {
  return (
    <div
      className={`rounded-[28px] border p-5 shadow-xl transition ${
        dark
          ? "border-white/10 bg-white/5"
          : "border-[#D3CBB8] bg-[#FAF8F5]"
      }`}
    >
      <div className="flex items-center justify-between">
        <p className={`text-sm ${dark ? "text-slate-400" : "text-stone-500"}`}>
          {label}
        </p>
        <span className="text-lg">{icon}</span>
      </div>
      <p className="mt-3 text-2xl font-semibold leading-7">{value}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Insight Agent Component
// ---------------------------------------------------------------------------

export default function InsightAgent({ theme }) {
  const dark = theme === "dark";

  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters & Search
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("All");

  // ------ Load insights ------
  const loadInsights = async () => {
    try {
      setLoading(true);
      const data = await getInsights();
      setInsights(data.insights || []);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to load insights.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInsights();
  }, []);

  // ------ Stats ------
  const stats = useMemo(() => {
    const total = insights.length;
    const highPriority = insights.filter((i) => i.priority === "high").length;
    const actionRequired = insights.filter(
      (i) => i.priority === "high" || i.priority === "medium"
    ).length;
    const informational = insights.filter((i) => i.priority === "low").length;
    return { total, highPriority, actionRequired, informational };
  }, [insights]);

  // ------ Filtered insights ------
  const filteredInsights = useMemo(() => {
    let filtered = [...insights];

    if (search.trim()) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (i) =>
          i.title?.toLowerCase().includes(q) ||
          i.description?.toLowerCase().includes(q) ||
          i.source?.toLowerCase().includes(q)
      );
    }

    if (sourceFilter !== "All") {
      filtered = filtered.filter((i) => i.source === sourceFilter);
    }
    if (priorityFilter !== "All") {
      filtered = filtered.filter((i) => i.priority === priorityFilter);
    }

    // Sort: high priority first, then by detected_at descending
    filtered.sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      const pDiff =
        (priorityOrder[a.priority] ?? 2) - (priorityOrder[b.priority] ?? 2);
      if (pDiff !== 0) return pDiff;
      return new Date(b.detected_at || 0) - new Date(a.detected_at || 0);
    });

    return filtered;
  }, [insights, search, sourceFilter, priorityFilter]);

  // ------ Styling helpers ------
  const inputClass = dark
    ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40"
    : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800 placeholder:text-stone-400 focus:border-clay";

  const badgeClass = dark
    ? "border-white/10 bg-white/5 text-slate-300"
    : "border-[#D3CBB8] bg-[#F3EFE4] text-stone-600";

  const activeBadgeClass = dark
    ? "border-cyan-400/60 bg-cyan-500/20 text-cyan-300"
    : "border-clay bg-clay/15 text-clay font-semibold";

  return (
    <div className="space-y-6">
      {/* ---- Summary Stats Grid ---- */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon="💡"
          label="Total Insights"
          value={stats.total}
          dark={dark}
        />
        <StatCard
          icon="🔴"
          label="High Priority"
          value={stats.highPriority}
          dark={dark}
        />
        <StatCard
          icon="⚡"
          label="Action Required"
          value={stats.actionRequired}
          dark={dark}
        />
        <StatCard
          icon="ℹ️"
          label="Informational"
          value={stats.informational}
          dark={dark}
        />
      </div>

      {/* ---- Main Card: Title + Search ---- */}
      <ResultCard
        title="Insight Agent"
        subtitle="AI-generated insights from Email Intelligence, Meeting Intelligence, Organizational Knowledge, and Analytics."
        theme={theme}
      >
        {/* ---- Error banner ---- */}
        {error ? (
          <div className="mb-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        ) : null}

        {/* ---- Search / Filter Input ---- */}
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search insights by keyword, title, or source..."
          className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition ${inputClass}`}
        />
      </ResultCard>

      {/* ---- Filter Chips ---- */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Source filters */}
        <span
          className={`text-xs font-semibold uppercase tracking-[0.2em] ${dark ? "text-slate-400" : "text-stone-500"}`}
        >
          Source:
        </span>
        {SOURCES.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSourceFilter(s)}
            className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
              sourceFilter === s ? activeBadgeClass : badgeClass
            }`}
          >
            {s === "All" ? "All" : (SOURCE_CONFIG[s]?.icon || "") + " " + s}
          </button>
        ))}

        {/* Priority filters */}
        <span
          className={`ml-2 text-xs font-semibold uppercase tracking-[0.2em] ${dark ? "text-slate-400" : "text-stone-500"}`}
        >
          Priority:
        </span>
        {PRIORITIES.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setPriorityFilter(p)}
            className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
              priorityFilter === p ? activeBadgeClass : badgeClass
            }`}
          >
            {p === "All" ? "All" : PRIORITY_CONFIG[p]?.label}
          </button>
        ))}

        {/* Clear filters */}
        {(sourceFilter !== "All" || priorityFilter !== "All" || search.trim() !== "") && (
          <button
            type="button"
            onClick={() => {
              setSearch("");
              setSourceFilter("All");
              setPriorityFilter("All");
            }}
            className={`ml-auto rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
              dark
                ? "border-rose-400/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20"
                : "border-rose-300 bg-rose-50 text-rose-700 hover:bg-rose-100"
            }`}
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* ---- Insight Cards ---- */}
      {loading ? (
        <ResultCard title="Insights" subtitle="Loading…" theme={theme}>
          <div className="rounded-2xl border border-dashed px-4 py-8 text-center text-sm text-slate-400">
            Loading insights…
          </div>
        </ResultCard>
      ) : filteredInsights.length === 0 ? (
        <ResultCard title="Insights" subtitle="No results" theme={theme}>
          <div className="rounded-2xl border border-dashed px-4 py-8 text-center text-sm text-slate-400">
            {insights.length === 0
              ? "No insights available. AI agents are scanning your data sources…"
              : "No insights match your current filters or search term."}
          </div>
        </ResultCard>
      ) : (
        <div className="grid gap-4">
          {filteredInsights.map((insight, idx) => {
            const sourceConfig = SOURCE_CONFIG[insight.source] || {
              icon: "💡",
              label: insight.source,
              color: {
                dark: "bg-slate-500/15 text-slate-300 border-slate-400/30",
                light: "bg-stone-100 text-stone-600 border-stone-300",
              },
            };
            const priorityConfig = PRIORITY_CONFIG[insight.priority] || PRIORITY_CONFIG.medium;
            const srcColor = dark ? sourceConfig.color.dark : sourceConfig.color.light;
            const priColor = dark ? priorityConfig.color.dark : priorityConfig.color.light;
            const dotColor = dark ? priorityConfig.dot : priorityConfig.dotLight;

            return (
              <div
                key={insight.id || idx}
                className={`rounded-[28px] border p-5 shadow-xl backdrop-blur-xl transition-all hover:scale-[1.005] md:p-6 ${
                  dark
                    ? "border-white/10 bg-white/5"
                    : "border-[#D3CBB8] bg-[#FAF8F5]"
                }`}
              >
                <div className="flex flex-col gap-4">
                  {/* Top row: icon + title + time */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <span className="mt-0.5 text-xl shrink-0">
                        {sourceConfig.icon}
                      </span>
                      <div className="min-w-0 flex-1">
                        <h3
                          className={`text-base font-semibold ${
                            dark ? "text-slate-100" : "text-stone-800"
                          }`}
                        >
                          {insight.title}
                        </h3>
                        <p
                          className={`mt-1 text-sm leading-6 ${
                            dark ? "text-slate-400" : "text-stone-500"
                          }`}
                        >
                          {insight.description}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`shrink-0 text-xs whitespace-nowrap ${
                        dark ? "text-slate-500" : "text-stone-400"
                      }`}
                    >
                      {formatDetectedAt(insight.detected_at)}
                    </span>
                  </div>

                  {/* Bottom row: badges */}
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Source badge */}
                    <span
                      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.1em] ${srcColor}`}
                    >
                      {sourceConfig.icon} {sourceConfig.label}
                    </span>

                    {/* Priority badge */}
                    <span
                      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.1em] ${priColor}`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
                      {priorityConfig.label}
                    </span>

                    {/* Time badge (for mobile clarity) */}
                    <span
                      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${
                        dark
                          ? "border-white/10 bg-white/5 text-slate-400"
                          : "border-[#D3CBB8] bg-[#F3EFE4] text-stone-500"
                      }`}
                    >
                      🕐 {formatDetectedAt(insight.detected_at)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
