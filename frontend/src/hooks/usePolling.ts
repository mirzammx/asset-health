import { useEffect, useState } from "react";

/** Calls `fetcher` now and every `intervalMs`; refetches when `deps` change. */
export function usePolling<T>(fetcher: () => Promise<T>, deps: unknown[], intervalMs = 15000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const d = await fetcher();
        if (alive) { setData(d); setError(null); }
      } catch (e) {
        if (alive) setError(String(e));
      }
    };
    setData(null);
    load();
    const id = setInterval(load, intervalMs);
    return () => { alive = false; clearInterval(id); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error };
}
