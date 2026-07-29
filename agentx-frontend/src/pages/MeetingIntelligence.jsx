import { useState } from "react";
import ApiResponsePanel from "../components/ApiResponsePanel";
import ResultCard from "../components/ResultCard";
import { summarizeMeeting } from "../services/api";
import { downloadPdf, shareViaEmail } from "../utils/exportPdf";
import { usePageState } from "../context/PageStateContext";

function renderItems(items, theme) {
  const dark = theme === 'dark'
  if (!items?.length)
    return <p className={`text-sm ${dark ? 'text-slate-400' : 'text-stone-500'}`}>No items returned.</p>;

  return (
    <ul className={`space-y-2 text-sm leading-7 ${dark ? 'text-slate-300' : 'text-stone-700'}`}>
      {items.map((item, index) => (
        <li
          key={`${String(item)}-${index}`}
          className={`rounded-2xl border px-4 py-3 ${
            dark ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5]'
          }`}
        >
          {typeof item === "object" ? JSON.stringify(item) : item}
        </li>
      ))}
    </ul>
  );
}

export default function MeetingIntelligence({ theme }) {
  const [pageState, setPageState] = usePageState("meeting-intelligence");
  const transcript = pageState?.transcript ?? "";
  const result = pageState?.result ?? null;
  const setTranscript = (v) => setPageState((s) => ({ ...s, transcript: v }));
  const setResult = (v) => setPageState((s) => ({ ...s, result: v }));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    if (!transcript.trim()) {
      setError("Please paste a meeting transcript first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await summarizeMeeting(transcript);
      setResult(response);
    } catch (err) {
      setError(err.message || "Unable to generate meeting summary.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = () => {
    if (!result) return;
    downloadPdf({
      title: "Meeting Intelligence Summary",
      subtitle: "AI-generated Meeting Insights & Action Items",
      filename: "meeting_intelligence_summary.pdf",
      sections: [
        {
          title: "Executive Summary",
          content: result.summary || "No summary generated.",
        },
        {
          title: "Decisions",
          content: result.decisions || [],
        },
        {
          title: "Action Items",
          content: result.actions || result.action_items || [],
        },
        {
          title: "Next Steps",
          content: result.next_steps || [],
        },
      ],
    });
  };

  return (
    <div className="space-y-6">
      <ResultCard
        title="Meeting Intelligence"
        subtitle="Summarize transcripts and surface decisions, action items, and next steps."
        theme={theme}
        actions={
          <div className="flex flex-wrap gap-2">
            {result ? (
              <button
                type="button"
                onClick={handleDownloadPdf}
                className={`flex items-center gap-2 rounded-2xl border px-4 py-2 text-sm font-semibold transition ${
                  theme === 'dark'
                    ? 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20'
                    : 'border-clay/30 bg-clay/10 text-clay hover:bg-clay/20'
                }`}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download PDF
              </button>
            ) : null}
            <button
              type="button"
              onClick={submit}
              disabled={loading}
              className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                theme === 'dark' ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300' : 'bg-clay text-white hover:bg-clay/90'
              }`}
            >
              {loading ? "Generating…" : "Generate Summary"}
            </button>
          </div>
        }
      >
        <textarea
          value={transcript}
          onChange={(event) => setTranscript(event.target.value)}
          placeholder="Paste your meeting transcript here..."
          className={`min-h-[240px] w-full rounded-[28px] border px-5 py-4 text-sm outline-none transition ${
            theme === "dark"
              ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40"
              : "border-[#D3CBB8] bg-[#FAF8F5] text-stone-800 placeholder:text-stone-400 focus:border-clay"
          }`}
        />
        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </div>
        ) : null}
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-2">
        <ResultCard title="Summary" subtitle="Executive recap" theme={theme}>
          <p className={`text-sm leading-7 ${theme === 'dark' ? 'text-slate-300' : 'text-stone-700'}`}>
            {result?.summary || "No summary generated yet."}
          </p>
        </ResultCard>
        <ResultCard
          title="Decisions"
          subtitle="Committed choices"
          theme={theme}
        >
          {renderItems(result?.decisions, theme)}
        </ResultCard>
        <ResultCard
          title="Action Items"
          subtitle="Assigned or implied work"
          theme={theme}
        >
          {renderItems(result?.actions || result?.action_items, theme)}
        </ResultCard>
        <ResultCard
          title="Next Steps"
          subtitle="Follow-up momentum"
          theme={theme}
        >
          {renderItems(result?.next_steps, theme)}
        </ResultCard>
      </div>

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  );
}
