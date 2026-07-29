import { useState } from "react";
import ApiResponsePanel from "../components/ApiResponsePanel";
import ResultCard from "../components/ResultCard";
import { generateResearch } from "../services/api";
import { downloadPdf, shareViaEmail } from "../utils/exportPdf";
import { usePageState } from "../context/PageStateContext";

function parseJsonIfNeeded(value) {
  if (typeof value === "string") {
    const trimmed = value.trim();
    if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
      try {
        return JSON.parse(trimmed);
      } catch (e) {
        return value;
      }
    }
  }
  return value;
}

function normalizeResult(rawResult) {
  if (!rawResult) return null;
  let res = parseJsonIfNeeded(rawResult);

  if (typeof res === "string") {
    // If the entire result is a raw text response, place it into overview
    return {
      overview: res,
      outline: [],
      key_concepts: [],
      research_questions: [],
      citations: [],
    };
  }

  // Parse any individual nested JSON string properties
  const overview = typeof res.overview === "object" ? JSON.stringify(res.overview) : (res.overview || "");
  const outline = Array.isArray(parseJsonIfNeeded(res.outline)) ? parseJsonIfNeeded(res.outline) : (res.outline ? [res.outline] : []);
  const key_concepts = Array.isArray(parseJsonIfNeeded(res.key_concepts)) ? parseJsonIfNeeded(res.key_concepts) : (res.key_concepts ? [res.key_concepts] : []);
  const research_questions = Array.isArray(parseJsonIfNeeded(res.research_questions)) ? parseJsonIfNeeded(res.research_questions) : (res.research_questions ? [res.research_questions] : []);
  const citations = Array.isArray(parseJsonIfNeeded(res.citations)) ? parseJsonIfNeeded(res.citations) : (res.citations ? [res.citations] : []);

  return {
    overview,
    outline,
    key_concepts,
    research_questions,
    citations,
  };
}

function renderTextValue(val) {
  if (val === null || val === undefined) return "";
  const parsed = parseJsonIfNeeded(val);
  if (typeof parsed === "string" || typeof parsed === "number" || typeof parsed === "boolean") {
    return String(parsed);
  }
  if (Array.isArray(parsed)) {
    return parsed.map(renderTextValue).filter(Boolean).join(" • ");
  }
  if (typeof parsed === "object") {
    return Object.entries(parsed)
      .map(([k, v]) => {
        const keyName = k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
        const formattedVal = renderTextValue(v);
        return formattedVal ? `${keyName}: ${formattedVal}` : null;
      })
      .filter(Boolean)
      .join(" | ");
  }
  return String(parsed);
}

function renderItemContent(item) {
  const parsed = parseJsonIfNeeded(item);
  if (typeof parsed === "object" && parsed !== null) {
    if (Array.isArray(parsed)) {
      return (
        <div className="space-y-1">
          {parsed.map((sub, i) => (
            <div key={i}>{renderItemContent(sub)}</div>
          ))}
        </div>
      );
    }

    const title = parsed.title || parsed.name || parsed.topic || parsed.heading || parsed.concept;
    const desc = parsed.description || parsed.details || parsed.summary || parsed.content || parsed.text || parsed.question || parsed.citation;
    const extraEntries = Object.entries(parsed).filter(
      ([k]) => !['title', 'name', 'topic', 'heading', 'concept', 'description', 'details', 'summary', 'content', 'text', 'question', 'citation'].includes(k)
    );

    return (
      <div className="space-y-1">
        {title ? <div className="font-semibold text-stone-800 dark:text-slate-100">{renderTextValue(title)}</div> : null}
        {desc ? <div className="text-sm leading-relaxed text-stone-600 dark:text-slate-300">{renderTextValue(desc)}</div> : null}
        {!title && !desc ? (
          <div className="text-sm leading-relaxed text-stone-600 dark:text-slate-300">
            {renderTextValue(parsed)}
          </div>
        ) : null}
        {extraEntries.length > 0 && (title || desc) ? (
          <div className="mt-2 text-xs space-y-1 opacity-90 border-t border-slate-200 dark:border-white/10 pt-2">
            {extraEntries.map(([k, v]) => {
              const label = k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
              return (
                <div key={k} className="flex flex-wrap gap-1">
                  <span className="font-medium text-stone-700 dark:text-slate-300">{label}:</span>
                  <span className="text-stone-600 dark:text-slate-400">{renderTextValue(v)}</span>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    );
  }
  return String(parsed);
}


function renderList(items, theme) {
  const dark = theme === 'dark';
  const parsedItems = parseJsonIfNeeded(items);
  const listArray = Array.isArray(parsedItems) ? parsedItems : (parsedItems ? [parsedItems] : []);

  if (!listArray.length)
    return <p className={`text-sm ${dark ? 'text-slate-400' : 'text-stone-500'}`}>No data yet.</p>;

  return (
    <ul className={`space-y-2 text-sm leading-7 ${dark ? 'text-slate-300' : 'text-stone-700'}`}>
      {listArray.map((item, index) => (
        <li
          key={`${typeof item === 'object' ? JSON.stringify(item) : String(item)}-${index}`}
          className={`rounded-2xl border px-4 py-3 ${
            dark ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5]'
          }`}
        >
          {renderItemContent(item)}
        </li>
      ))}
    </ul>
  );
}

export default function ResearchCopilot({ theme }) {
  const [pageState, setPageState] = usePageState("research-copilot");
  const topic = pageState?.topic ?? "";
  const result = pageState?.result ?? null;
  const setTopic = (v) => setPageState((s) => ({ ...s, topic: v }));
  const setResult = (v) => setPageState((s) => ({ ...s, result: v }));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    if (!topic.trim()) {
      setError("Please enter a research topic.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await generateResearch(topic);
      setResult(normalizeResult(response));
    } catch (err) {
      setError(err.message || "Unable to generate research package.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = () => {
    if (!result) return;
    downloadPdf({
      title: `Research Report: ${topic || 'Research Copilot'}`,
      subtitle: "Structured Academic & Market Research Framework",
      filename: "research_copilot_report.pdf",
      sections: [
        {
          title: "Overview",
          content: result.overview || "No overview generated.",
        },
        {
          title: "Outline",
          content: result.outline || [],
        },
        {
          title: "Key Concepts",
          content: result.key_concepts || [],
        },
        {
          title: "Research Questions",
          content: result.research_questions || [],
        },
        {
          title: "Citations",
          content: result.citations || [],
        },
      ],
    });
  };

  const handleShareEmail = () => {
    if (!result) return;
    const body = `Hi,\n\nHere is the research report for "${topic || 'Research Topic'}":\n\n=== OVERVIEW ===\n${result.overview || 'N/A'}\n\n=== OUTLINE ===\n${(result.outline || []).map((x) => `• ${typeof x === 'object' ? JSON.stringify(x) : x}`).join('\n')}\n\n=== KEY CONCEPTS ===\n${(result.key_concepts || []).map((x) => `• ${typeof x === 'object' ? JSON.stringify(x) : x}`).join('\n')}\n\n=== RESEARCH QUESTIONS ===\n${(result.research_questions || []).map((x) => `• ${typeof x === 'object' ? JSON.stringify(x) : x}`).join('\n')}\n\n=== CITATIONS ===\n${(result.citations || []).map((x) => `• ${typeof x === 'object' ? JSON.stringify(x) : x}`).join('\n')}\n\n---\nSent via AgentX Research Copilot`;

    shareViaEmail({
      subject: `Research Report: ${topic || 'Research Copilot'}`,
      body,
    });
  };

  return (
    <div className="space-y-6">
      <ResultCard
        title="Research Copilot"
        subtitle="Generate structured academic or market research frameworks from a single prompt."
        theme={theme}
        actions={
          <div className="flex flex-wrap gap-2">
            {result ? (
              <>
                <button
                  type="button"
                  onClick={handleShareEmail}
                  className={`flex items-center gap-2 rounded-2xl border px-4 py-2 text-sm font-semibold transition ${
                    theme === 'dark'
                      ? 'border-purple-500/30 bg-purple-500/10 text-purple-300 hover:bg-purple-500/20'
                      : 'border-clay/30 bg-clay/10 text-clay hover:bg-clay/20'
                  }`}
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 002-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Share via Email
                </button>
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
              </>
            ) : null}
            <button
              type="button"
              onClick={submit}
              disabled={loading}
              className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                theme === 'dark' ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300' : 'bg-clay text-white hover:bg-clay/90'
              }`}
            >
              {loading ? "Generating…" : "Generate Research"}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Enter a research topic..."
            className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none transition ${
              theme === "dark"
                ? "border-white/10 bg-slate-950/70 text-slate-50 placeholder:text-slate-500 focus:border-cyan-400/40"
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

      <div className="grid gap-6 xl:grid-cols-2">
        <ResultCard
          title="Overview"
          subtitle="High-level framing"
          theme={theme}
        >
          <p className={`text-sm leading-7 ${theme === 'dark' ? 'text-slate-300' : 'text-stone-700'}`}>
            {result?.overview || "No overview generated yet."}
          </p>
        </ResultCard>
        <ResultCard
          title="Outline"
          subtitle="Suggested research structure"
          theme={theme}
        >
          {renderList(result?.outline, theme)}
        </ResultCard>
        <ResultCard
          title="Key Concepts"
          subtitle="Important ideas to explore"
          theme={theme}
        >
          {renderList(result?.key_concepts, theme)}
        </ResultCard>
        <ResultCard
          title="Research Questions"
          subtitle="What to investigate"
          theme={theme}
        >
          {renderList(result?.research_questions, theme)}
        </ResultCard>
      </div>

      <ResultCard
        title="Citations"
        
        theme={theme}
      >
        {renderList(result?.citations, theme)}
      </ResultCard>

      {/* <ApiResponsePanel data={result} theme={theme} /> */}
    </div>
  );
}
