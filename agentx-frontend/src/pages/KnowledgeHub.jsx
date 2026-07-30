import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import ResultCard from "../components/ResultCard";
import NextRecommendedStepCard from "../components/NextRecommendedStepCard";
import { searchKnowledgeHub } from "../services/api";

export default function KnowledgeHub({ theme }) {
  const location = useLocation();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [entries, setEntries] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  const dark = theme === "dark";

  const executeSearch = useCallback(async (searchTerm) => {
    const trimmed = searchTerm.trim();
    if (!trimmed) {
      setError("Please enter a search term.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await searchKnowledgeHub(trimmed);
      setEntries(response?.entries || []);
      setHasSearched(true);
    } catch (err) {
      setError(err.message || "Unable to search the knowledge hub.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSearch = () => {
    executeSearch(query);
  };

  useEffect(() => {
    if (location.state?.query) {
      const passedQuery = location.state.query;
      setQuery(passedQuery);
      executeSearch(passedQuery);
    }
  }, [location.state, executeSearch]);

  return (
    <div className="space-y-6">
      <ResultCard
        title="Knowledge Hub"
        subtitle="Search saved insights, meeting notes, and stored knowledge snippets."
        theme={theme}
        actions={
          <button
            type="button"
            onClick={handleSearch}
            disabled={loading}
            className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${dark
              ? "bg-amber-400 text-slate-950 hover:bg-amber-300"
              : "bg-clay text-white hover:bg-clay/90"
              }`}
          >
            {loading ? "Searching…" : "Search Hub"}
          </button>
        }
      >
        <div className="space-y-4">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleSearch();
              }
            }}
            placeholder="Search the knowledge hub..."
            className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition ${dark
              ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-amber-400/40"
              : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800 placeholder:text-stone-400 focus:border-clay"
              }`}
          />
          {error ? (
            <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
              {error}
            </div>
          ) : null}
        </div>
      </ResultCard>

      <div className="grid gap-4">
        {entries.length === 0 ? (
          <ResultCard title="Results" subtitle="No results yet" theme={theme}>
            <p
              className={`text-sm ${dark ? "text-slate-300" : "text-stone-700"}`}
            >
              Search for a topic to surface recent entries from the shared
              knowledge base.
            </p>
          </ResultCard>
        ) : (
          entries.map((entry, index) => (
            <ResultCard
              key={`${entry.title || entry.type || "entry"}-${index}`}
              title={entry.title || "Knowledge Entry"}
              subtitle={`Source: ${entry.source || entry.type || "Knowledge Hub"}`}
              theme={theme}
              actions={
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${dark
                    ? "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                    : "bg-clay/10 text-clay border border-clay/30"
                    }`}
                >
                  {entry.source || entry.type || "Knowledge Hub"}
                </span>
              }
            >
              <p
                className={`text-sm leading-7 ${dark ? "text-slate-300" : "text-stone-700"}`}
              >
                {entry.summary || "No summary available."}
              </p>
            </ResultCard>
          ))
        )}
      </div>

      {(hasSearched || entries.length > 0 || query.trim().length > 0) && (
        <NextRecommendedStepCard
          stepNumber="Step 3 of 3"
          icon="💡"
          title="Next Recommended Step: Insight Agent"
          description="Synthesize cross-channel insights and explore AI recommendations compiled from Meeting, Email, and Knowledge bases."
          targetPath="/insights"
          targetLabel="Proceed to Insight Agent →"
          stateData={{ sourceFilter: "Meeting", search: query }}
          dataPreview={`Filter Insights by Source: "Meeting" & Search: "${query}"`}
          theme={theme}
        />
      )}
    </div>
  );
}
