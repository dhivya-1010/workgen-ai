import ModuleCard from '../components/ModuleCard'
import ResultCard from '../components/ResultCard'

export default function Dashboard({ items, onNavigate, theme }) {
  const featured = items.filter((item) => item.featured)

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
        <div className="rounded-[32px] border border-cyan-400/15 bg-gradient-to-br from-cyan-500/15 via-slate-900/20 to-violet-500/15 p-8 shadow-2xl backdrop-blur-xl">
          <div className="inline-flex rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-300">
            AgentX mission control
          </div>
          <h2 className="mt-5 max-w-3xl text-3xl font-semibold tracking-tight md:text-5xl">
            Demo-ready AI operations cockpit for email, meetings, research, journaling, and live audio.
          </h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 md:text-base">
            This frontend keeps your existing Python backend untouched and focuses on presenting every AgentX module in a clean, hackathon-friendly experience.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => onNavigate('email')}
              className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/25 transition hover:bg-cyan-300"
            >
              Launch Email Intelligence
            </button>
            <button
              type="button"
              onClick={() => onNavigate('meeting')}
              className="rounded-2xl border border-white/15 bg-white/8 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/12"
            >
              Open Meeting Intelligence
            </button>
          </div>
        </div>

        <ResultCard title="Why this works for demos" subtitle="Pitch-ready product framing" theme={theme}>
          <div className="grid gap-3 text-sm text-slate-300">
            {[
              'One dashboard for all AI workflows',
              'Clear backend API integration points',
              'Dark/light theme for stage-friendly presentation',
              'Focused module pages with action-oriented layouts',
            ].map((point) => (
              <div
                key={point}
                className={`rounded-2xl border px-4 py-3 ${
                  theme === 'dark' ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-slate-50 text-slate-600'
                }`}
              >
                {point}
              </div>
            ))}
          </div>
        </ResultCard>
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {featured.map((item) => (
          <ModuleCard
            key={item.id}
            title={item.label}
            description={item.description}
            icon={item.icon}
            accent={item.accent}
            theme={theme}
            onClick={() => onNavigate(item.id)}
          />
        ))}
      </section>
    </div>
  )
}