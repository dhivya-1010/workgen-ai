import { createContext, useCallback, useContext, useState } from "react";

// ─── Context ───────────────────────────────────────────────────────────────
const PageStateContext = createContext(null);

// ─── Provider ──────────────────────────────────────────────────────────────
export function PageStateProvider({ children }) {
  // Each page key maps to whatever state that page wants to persist.
  const [store, setStore] = useState({});

  const getPageState = useCallback(
    (pageKey) => store[pageKey] ?? null,
    [store],
  );

  const setPageState = useCallback((pageKey, value) => {
    setStore((prev) => ({
      ...prev,
      [pageKey]: typeof value === "function" ? value(prev[pageKey] ?? null) : value,
    }));
  }, []);

  return (
    <PageStateContext.Provider value={{ getPageState, setPageState }}>
      {children}
    </PageStateContext.Provider>
  );
}

// ─── Hook ──────────────────────────────────────────────────────────────────
export function usePageState(pageKey) {
  const ctx = useContext(PageStateContext);
  if (!ctx) throw new Error("usePageState must be used within PageStateProvider");
  const { getPageState, setPageState } = ctx;

  const state = getPageState(pageKey);
  const setState = useCallback(
    (value) => setPageState(pageKey, value),
    [pageKey, setPageState],
  );

  return [state, setState];
}
