import { useEffect, useMemo, useState } from "react";
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import EmailIntelligence from "./pages/EmailIntelligence";
import InstitutionalPlatform from "./pages/InstitutionalPlatform";

const NAV_ITEMS = [
  {
    id: "home",
    path: "/",
    label: "Home",
    caption: "VAZ",
    icon: "◈",
    description: "Meet VAZ, the voice-first dashboard assistant.",
    accent: "from-slate-500/20 to-slate-900/10",
  },
  {
    id: "study",
    path: "/study",
    label: "Institutional Study Platform",
    caption: "Knowledge + Study Buddy",
    icon: "🗂️",
    description: "Knowledge Hub, canonical answers, faculty review, student tutoring, evaluation, and institution administration.",
    accent: "from-emerald-500/30 via-amber-500/15 to-teal-500/10",
  },
  {
    id: "email",
    path: "/email",
    label: "Email Intelligence",
    caption: "Inbox",
    icon: "✉️",
    description:
      "Scan inboxes, classify intent, and push detected opportunities into action.",
    accent: "from-amber-500/30 via-yellow-500/15 to-blue-500/10",
  },
  {
    accent: "from-emerald-500/30 via-amber-500/15 to-teal-500/10",
  },
];

export default function App() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem("agentx-theme") || "dark",
  );
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    localStorage.setItem("agentx-theme", theme);
    const root = document.documentElement;
    const body = document.body;
    const metaTheme = document.querySelector('meta[name="theme-color"]');

    if (theme === "dark") {
      root.classList.add("dark");
      root.classList.remove("light-theme");
      body.classList.add("dark");
      body.classList.remove("light-theme");
      if (metaTheme) metaTheme.setAttribute("content", "#020617");
    } else {
      root.classList.remove("dark");
      root.classList.add("light-theme");
      body.classList.remove("dark");
      body.classList.add("light-theme");
      if (metaTheme) metaTheme.setAttribute("content", "#f3efe4");
    }
  }, [theme]);

  const activePath = location.pathname || "/";
  const activeItem = useMemo(
    () => NAV_ITEMS.find((item) => item.path === activePath) || NAV_ITEMS[0],
    [activePath],
  );

  const dark = theme === "dark";
  const isDashboard = activePath === "/";

  const pageElement = (PageComponent) => <PageComponent theme={theme} />;

  useEffect(() => {
    if (activePath !== "/") {
      window.speechSynthesis?.cancel?.();
    }
  }, [activePath]);

  return (
    <div
      className={`relative min-h-screen w-full transition-colors ${dark
        ? "bg-slate-950 text-slate-50"
        : "light-theme bg-paper-grid text-[#23201C]"
        }`}
    >
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div
          className={`absolute -left-16 top-10 h-64 w-64 rounded-full blur-3xl ${dark ? "bg-amber-500/12" : "bg-clay/5"}`}
        />
        <div
          className={`absolute right-0 top-1/3 h-72 w-72 rounded-full blur-3xl ${dark ? "bg-yellow-500/12" : "bg-forest/5"}`}
        />
        <div
          className={`absolute bottom-0 left-1/3 h-72 w-72 rounded-full blur-3xl ${dark ? "bg-yellow-500/10" : "bg-clay/5"}`}
        />
      </div>

      <div className="relative flex min-h-screen flex-col md:flex-row">
        <Sidebar
          items={NAV_ITEMS}
          activePath={activePath}
          onNavigate={navigate}
          theme={theme}
        />

        <main className="flex-1 flex flex-col p-4 md:p-6 lg:p-8">
          {!isDashboard ? (
            <header className="mb-6 flex flex-col gap-4 lg:mb-8 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p
                  className={`text-sm font-semibold uppercase tracking-[0.28em] ${dark ? "text-amber-400" : "text-forest"}`}
                >
                  {activeItem.caption}
                </p>
                <h2 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">
                  {activeItem.label}
                </h2>
                <p
                  className={`mt-2 max-w-3xl text-sm leading-7 ${dark ? "text-slate-300" : "text-[#5F5852]"}`}
                >
                  {activeItem.description}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => setTheme(dark ? "light" : "dark")}
                  className={`rounded-2xl border px-4 py-3 text-sm font-medium shadow-lg backdrop-blur-xl transition ${dark
                    ? "border-white/10 bg-white/5 hover:bg-white/10"
                    : "border-[#D3CBB8] bg-[#FAF8F5]/85 hover:bg-[#F3EFE4] text-slate-800"
                    }`}
                >
                  {dark ? "☀️ Light theme" : "🌙 Dark theme"}
                </button>
              </div>
            </header>
          ) : null}

          <Routes>
            <Route
              path="/"
              element={<Dashboard theme={theme} onNavigate={navigate} />}
            />
            <Route path="/email" element={pageElement(EmailIntelligence)} />
            <Route path="/study" element={pageElement(InstitutionalPlatform)} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
