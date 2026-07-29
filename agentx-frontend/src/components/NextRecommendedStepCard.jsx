import React from "react";
import { useNavigate } from "react-router-dom";

export default function NextRecommendedStepCard({
  stepNumber,
  title = "Next Recommended Step",
  description,
  targetPath,
  targetLabel = "Continue →",
  stateData = {},
  icon = "⚡",
  theme = "dark",
  badge = "Guided Workflow",
  dataPreview,
}) {
  const navigate = useNavigate();
  const dark = theme === "dark";

  const handleNavigate = () => {
    if (!targetPath) return;
    navigate(targetPath, { state: stateData });
  };

  return (
    <div
      className={`relative overflow-hidden rounded-[28px] border p-5 shadow-2xl backdrop-blur-xl transition-all duration-300 md:p-6 ${
        dark
          ? "border-cyan-500/30 bg-gradient-to-r from-cyan-950/40 via-slate-900/60 to-indigo-950/40 text-slate-100"
          : "border-clay/40 bg-gradient-to-r from-[#FAF6EF] via-[#F3EFE4] to-[#FAF8F5] text-stone-850"
      }`}
    >
      {/* Decorative accent glow */}
      <div
        className={`pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full blur-2xl ${
          dark ? "bg-cyan-500/15" : "bg-clay/10"
        }`}
      />

      <div className="relative flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2 flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                dark
                  ? "border-cyan-400/40 bg-cyan-500/10 text-cyan-300"
                  : "border-clay/40 bg-clay/15 text-clay"
              }`}
            >
              <span className="text-sm">{icon}</span>
              {badge}
            </span>
            {stepNumber && (
              <span
                className={`text-xs font-medium ${
                  dark ? "text-slate-400" : "text-stone-500"
                }`}
              >
                {stepNumber}
              </span>
            )}
          </div>

          <h4 className="text-lg font-bold tracking-tight">
            {title}
          </h4>

          {description && (
            <p
              className={`text-sm leading-relaxed ${
                dark ? "text-slate-300" : "text-stone-600"
              }`}
            >
              {description}
            </p>
          )}

          {dataPreview && (
            <div
              className={`mt-2 rounded-2xl border px-3 py-2 text-xs font-mono truncate max-w-xl ${
                dark
                  ? "border-white/10 bg-slate-950/50 text-slate-400"
                  : "border-stone-300/60 bg-stone-100/70 text-stone-600"
              }`}
            >
              <span className="font-semibold non-italic">Payload: </span>
              {dataPreview}
            </div>
          )}
        </div>

        <div className="shrink-0 pt-2 md:pt-0">
          <button
            type="button"
            onClick={handleNavigate}
            className={`group inline-flex items-center gap-2 rounded-2xl px-5 py-3 text-sm font-semibold shadow-lg transition-all transform hover:scale-105 active:scale-95 ${
              dark
                ? "bg-gradient-to-r from-cyan-400 to-sky-400 text-slate-950 hover:from-cyan-300 hover:to-sky-300 shadow-cyan-500/20"
                : "bg-clay text-white hover:bg-clay/90 shadow-clay/20"
            }`}
          >
            <span>{targetLabel}</span>
            <svg
              className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14 5l7 7m0 0l-7 7m7-7H3"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
