import { useEffect, useMemo, useState } from "react";
import ResultCard from "../components/ResultCard";
import {
  createFollowup,
  deleteFollowup,
  getFollowups,
  updateFollowup,
} from "../services/api";

const SOURCE_ICONS = {
  Email: "✉️",
  Meeting: "📅",
  Task: "✓",
};

const PRIORITY_COLORS = {
  high: {
    badge: "bg-rose-500/15 text-rose-300 border-rose-400/30",
    dot: "bg-rose-400",
  },
  medium: {
    badge: "bg-amber-500/15 text-amber-300 border-amber-400/30",
    dot: "bg-amber-400",
  },
  low: {
    badge: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
    dot: "bg-emerald-400",
  },
};

const PRIORITY_COLORS_LIGHT = {
  high: {
    badge: "bg-rose-100 text-rose-700 border-rose-300",
    dot: "bg-rose-500",
  },
  medium: {
    badge: "bg-amber-100 text-amber-700 border-amber-300",
    dot: "bg-amber-500",
  },
  low: {
    badge: "bg-emerald-100 text-emerald-700 border-emerald-300",
    dot: "bg-emerald-500",
  },
};

const SOURCE_COLORS = {
  Email: "bg-sky-500/15 text-sky-300 border-sky-400/30",
  Meeting: "bg-violet-500/15 text-violet-300 border-violet-400/30",
  Task: "bg-cyan-500/15 text-cyan-300 border-cyan-400/30",
};

const SOURCE_COLORS_LIGHT = {
  Email: "bg-sky-100 text-sky-700 border-sky-300",
  Meeting: "bg-violet-100 text-violet-700 border-violet-300",
  Task: "bg-cyan-100 text-cyan-700 border-cyan-300",
};

function getTodayISO() {
  return new Date().toISOString().split("T")[0];
}

function isOverdue(dueDate) {
  if (!dueDate) return false;
  return dueDate < getTodayISO();
}

export default function FollowUpAgent({ theme }) {
  const dark = theme === "dark";

  const [followups, setFollowups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // New follow-up form state
  const [showForm, setShowForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newSource, setNewSource] = useState("Task");
  const [newDueDate, setNewDueDate] = useState("");
  const [newPriority, setNewPriority] = useState("medium");

  // Search & filter
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all"); // "all" | "pending" | "completed"
  const [priorityFilter, setPriorityFilter] = useState("all"); // "all" | "high" | "medium" | "low"

  // Stats
  const stats = useMemo(() => {
    const total = followups.length;
    const completed = followups.filter((f) => f.status === "completed").length;
    const pending = total - completed;
    const overdue = followups.filter(
      (f) => f.status === "pending" && isOverdue(f.due_date),
    ).length;
    return { total, completed, pending, overdue };
  }, [followups]);

  // ---------- Load follow-ups ----------
  const loadFollowups = async () => {
    try {
      setLoading(true);
      const data = await getFollowups();
      setFollowups(data.followups || []);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to load follow-ups.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFollowups();
  }, []);

  // ---------- Create ----------
  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    try {
      await createFollowup({
        title: newTitle.trim(),
        source: newSource,
        due_date: newDueDate,
        priority: newPriority,
      });
      setNewTitle("");
      setNewSource("Task");
      setNewDueDate("");
      setNewPriority("medium");
      setShowForm(false);
      await loadFollowups();
    } catch (err) {
      setError(err.message || "Failed to create follow-up.");
    }
  };

  // ---------- Mark complete / pending ----------
  const toggleStatus = async (followup) => {
    try {
      const newStatus =
        followup.status === "completed" ? "pending" : "completed";
      await updateFollowup(followup.id, { status: newStatus });
      await loadFollowups();
    } catch (err) {
      setError(err.message || "Failed to update follow-up.");
    }
  };

  // ---------- Delete ----------
  const handleDelete = async (id) => {
    try {
      await deleteFollowup(id);
      await loadFollowups();
    } catch (err) {
      setError(err.message || "Failed to delete follow-up.");
    }
  };

  // ---------- Filtered & Sorted follow-ups ----------
  const filteredFollowups = useMemo(() => {
    let filtered = [...followups];

    // Search by title
    if (search.trim()) {
      const q = search.toLowerCase();
      filtered = filtered.filter((f) => f.title.toLowerCase().includes(q));
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((f) => f.status === statusFilter);
    }

    // Priority filter
    if (priorityFilter !== "all") {
      filtered = filtered.filter((f) => f.priority === priorityFilter);
    }

    // Sort: overdue first, then by due date ascending
    filtered.sort((a, b) => {
      const aOverdue = a.status === "pending" && isOverdue(a.due_date) ? 0 : 1;
      const bOverdue = b.status === "pending" && isOverdue(b.due_date) ? 0 : 1;
      if (aOverdue !== bOverdue) return aOverdue - bOverdue;
      // Then by due date (if both have dates)
      if (a.due_date && b.due_date) return a.due_date.localeCompare(b.due_date);
      if (a.due_date) return -1;
      if (b.due_date) return 1;
      return 0;
    });

    return filtered;
  }, [followups, search, statusFilter, priorityFilter]);

  // ------ Styling helpers ------
  const cardClass = dark
    ? "border-white/10 bg-white/5"
    : "border-[#D3CBB8] bg-[#FAF8F5]";

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
      {/* ---- Stats Grid ---- */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="⏳ Pending"
          value={stats.pending}
          theme={theme}
          dark={dark}
        />
        <StatCard
          label="✅ Completed"
          value={stats.completed}
          theme={theme}
          dark={dark}
        />
        <StatCard
          label="⚠️ Overdue"
          value={stats.overdue}
          theme={theme}
          dark={dark}
        />
        <StatCard
          label="📋 Total"
          value={stats.total}
          theme={theme}
          dark={dark}
        />
      </div>

      {/* ---- Main Card: Search + Add + Form ---- */}
      <ResultCard
        title="Follow-Up Agent"
        subtitle="Track pending follow-ups from emails, meetings, and tasks. Overdue items rise to the top."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={() => setShowForm(!showForm)}
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition ${
              dark
                ? "bg-cyan-400 text-slate-950 hover:bg-cyan-300"
                : "bg-clay text-white hover:bg-clay/90"
            }`}
          >
            {showForm ? "Cancel" : "+ New Follow-Up"}
          </button>
        }
      >
        {/* ---- Error banner ---- */}
        {error ? (
          <div className="mb-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        ) : null}

        {/* ---- New Follow-Up Form ---- */}
        {showForm && (
          <div
            className={`mb-6 rounded-[28px] border p-5 space-y-4 ${cardClass}`}
          >
            <h4 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">
              New Follow-Up
            </h4>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Follow-up title..."
                className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none ${inputClass}`}
              />
              <select
                value={newSource}
                onChange={(e) => setNewSource(e.target.value)}
                className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none ${inputClass}`}
              >
                <option value="Email">✉️ Email</option>
                <option value="Meeting">📅 Meeting</option>
                <option value="Task">✓ Task</option>
              </select>
              <input
                type="date"
                value={newDueDate}
                onChange={(e) => setNewDueDate(e.target.value)}
                className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none ${inputClass}`}
              />
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value)}
                className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none ${inputClass}`}
              >
                <option value="high">🔴 High</option>
                <option value="medium">🟡 Medium</option>
                <option value="low">🟢 Low</option>
              </select>
            </div>
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleCreate}
                disabled={!newTitle.trim()}
                className={`rounded-2xl px-6 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                  dark
                    ? "bg-cyan-400 text-slate-950 hover:bg-cyan-300"
                    : "bg-clay text-white hover:bg-clay/90"
                }`}
              >
                Create Follow-Up
              </button>
            </div>
          </div>
        )}

        {/* ---- Search Bar ---- */}
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search follow-ups..."
          className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none ${inputClass}`}
        />
      </ResultCard>

      {/* ---- Filter Chips ---- */}
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={`text-xs font-semibold uppercase tracking-[0.2em] ${dark ? "text-slate-400" : "text-stone-500"}`}
        >
          Status:
        </span>
        {["all", "pending", "completed"].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStatusFilter(s)}
            className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
              statusFilter === s ? activeBadgeClass : badgeClass
            }`}
          >
            {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}

        <span
          className={`ml-2 text-xs font-semibold uppercase tracking-[0.2em] ${dark ? "text-slate-400" : "text-stone-500"}`}
        >
          Priority:
        </span>
        {["all", "high", "medium", "low"].map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setPriorityFilter(p)}
            className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
              priorityFilter === p ? activeBadgeClass : badgeClass
            }`}
          >
            {p === "all" ? "All" : p.charAt(0).toUpperCase() + p.slice(1)}
          </button>
        ))}

        {(statusFilter !== "all" ||
          priorityFilter !== "all" ||
          search.trim()) && (
          <button
            type="button"
            onClick={() => {
              setSearch("");
              setStatusFilter("all");
              setPriorityFilter("all");
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

      {/* ---- Follow-Up Cards ---- */}
      {loading ? (
        <ResultCard title="Follow-Ups" subtitle="Loading…" theme={theme}>
          <div className="rounded-2xl border border-dashed px-4 py-8 text-center text-sm text-slate-400">
            Loading follow-ups…
          </div>
        </ResultCard>
      ) : filteredFollowups.length === 0 ? (
        <ResultCard title="Follow-Ups" subtitle="No results" theme={theme}>
          <div className="rounded-2xl border border-dashed px-4 py-8 text-center text-sm text-slate-400">
            {followups.length === 0
              ? "No follow-ups yet. Click '+ New Follow-Up' to get started."
              : "No follow-ups match your current filters."}
          </div>
        </ResultCard>
      ) : (
        <div className="grid gap-4">
          {filteredFollowups.map((followup) => {
            const overdue =
              followup.status === "pending" && isOverdue(followup.due_date);
            const completed = followup.status === "completed";
            const pc = dark ? PRIORITY_COLORS : PRIORITY_COLORS_LIGHT;
            const sc = dark ? SOURCE_COLORS : SOURCE_COLORS_LIGHT;

            return (
              <div
                key={followup.id}
                className={`rounded-[28px] border p-5 shadow-xl backdrop-blur-xl transition-all md:p-6 ${
                  completed
                    ? dark
                      ? "border-white/5 bg-white/3 opacity-60"
                      : "border-[#D3CBB8] bg-[#F3EFE4] opacity-60"
                    : overdue
                      ? dark
                        ? "border-rose-400/30 bg-rose-500/10 shadow-rose-500/10"
                        : "border-rose-300 bg-rose-50/80 shadow-rose-500/5"
                      : cardClass
                }`}
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  {/* Left: Info */}
                  <div className="flex items-start gap-4 min-w-0 flex-1">
                    {/* Checkbox */}
                    <button
                      type="button"
                      onClick={() => toggleStatus(followup)}
                      className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition ${
                        completed
                          ? dark
                            ? "border-emerald-400 bg-emerald-500/30 text-emerald-300"
                            : "border-emerald-500 bg-emerald-100 text-emerald-700"
                          : dark
                            ? "border-white/20 hover:border-cyan-400/50"
                            : "border-[#D3CBB8] hover:border-clay"
                      }`}
                    >
                      {completed && <span className="text-xs">✓</span>}
                    </button>

                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3
                          className={`text-base font-semibold truncate ${
                            completed
                              ? dark
                                ? "text-slate-500 line-through"
                                : "text-stone-400 line-through"
                              : dark
                                ? "text-slate-100"
                                : "text-stone-800"
                          }`}
                        >
                          {followup.title}
                        </h3>

                        {/* Overdue badge */}
                        {overdue && (
                          <span
                            className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.15em] ${
                              dark
                                ? "border-rose-400/40 bg-rose-500/20 text-rose-300"
                                : "border-rose-300 bg-rose-100 text-rose-700"
                            }`}
                          >
                            ⏰ Overdue
                          </span>
                        )}
                      </div>

                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        {/* Source badge */}
                        <span
                          className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.1em] ${sc[followup.source] || (dark ? "bg-slate-500/15 text-slate-300 border-slate-400/30" : "bg-stone-100 text-stone-600 border-stone-300")}`}
                        >
                          {SOURCE_ICONS[followup.source] || "📌"}{" "}
                          {followup.source}
                        </span>

                        {/* Priority badge */}
                        <span
                          className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.1em] ${(pc[followup.priority] || pc.medium).badge}`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${(pc[followup.priority] || pc.medium).dot}`}
                          />
                          {followup.priority}
                        </span>

                        {/* Due date */}
                        {followup.due_date && (
                          <span
                            className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${
                              overdue
                                ? dark
                                  ? "border-rose-400/30 bg-rose-500/10 text-rose-300"
                                  : "border-rose-300 bg-rose-50 text-rose-700"
                                : completed
                                  ? dark
                                    ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-300"
                                    : "border-emerald-300 bg-emerald-50 text-emerald-700"
                                  : badgeClass
                            }`}
                          >
                            📅{" "}
                            {new Date(
                              followup.due_date + "T00:00:00",
                            ).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right: Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => toggleStatus(followup)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                        completed
                          ? dark
                            ? "bg-amber-500/15 text-amber-300 hover:bg-amber-500/25"
                            : "bg-amber-100 text-amber-700 hover:bg-amber-200"
                          : dark
                            ? "bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25"
                            : "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                      }`}
                    >
                      {completed ? "Reopen" : "Complete"}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(followup.id)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                        dark
                          ? "bg-rose-500/15 text-rose-300 hover:bg-rose-500/25"
                          : "bg-rose-100 text-rose-700 hover:bg-rose-200"
                      }`}
                    >
                      Delete
                    </button>
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

// ---- Small reusable stat card ----
function StatCard({ label, value, theme, dark }) {
  return (
    <div
      className={`rounded-[28px] border p-5 shadow-xl transition ${
        dark
          ? "border-white/10 bg-white/5"
          : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-850"
      }`}
    >
      <p className={`text-sm ${dark ? "text-slate-400" : "text-stone-500"}`}>
        {label}
      </p>
      <p className="mt-3 text-lg font-semibold leading-7">{value}</p>
    </div>
  );
}
