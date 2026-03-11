export default function ModuleCard({ title, description, icon, accent, onClick, theme }) {
  const dark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={onClick}
      className={`group relative overflow-hidden rounded-[28px] border p-6 text-left transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${
        dark ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-white/85'
      }`}
    >
      <div className={`absolute inset-0 bg-gradient-to-br opacity-80 ${accent}`} />
      <div className="absolute inset-px rounded-[27px] bg-gradient-to-b from-white/10 to-transparent" />
      <div className="relative z-10">
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/15 bg-slate-950/40 text-2xl text-white shadow-lg shadow-slate-950/20">
          {icon}
        </div>
        <h3 className="text-xl font-semibold">{title}</h3>
        <p className={`mt-2 text-sm leading-6 ${dark ? 'text-slate-300' : 'text-slate-600'}`}>
          {description}
        </p>
        <div className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-cyan-300 group-hover:text-cyan-200">
          Open module <span aria-hidden="true">→</span>
        </div>
      </div>
    </button>
  )
}