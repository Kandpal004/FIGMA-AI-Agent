import { useEffect, useState } from "react";

/**
 * Phase 1 console: a single health panel that proves the frontend can reach the
 * FastAPI backend through the Vite proxy. Real design-run views arrive in later
 * phases; this exists to close the end-to-end loop today.
 */

interface HealthPayload {
  status: string;
  service: string;
  environment: string;
}

type Probe =
  | { state: "loading" }
  | { state: "ok"; data: HealthPayload }
  | { state: "error"; message: string };

export function App(): JSX.Element {
  const [probe, setProbe] = useState<Probe>({ state: "loading" });

  useEffect(() => {
    let cancelled = false;
    fetch("/api/health")
      .then(async (res) => {
        if (!res.ok) throw new Error(`Backend returned ${res.status}`);
        return (await res.json()) as HealthPayload;
      })
      .then((data) => {
        if (!cancelled) setProbe({ state: "ok", data });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setProbe({
            state: "error",
            message: err instanceof Error ? err.message : "Unknown error",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="shell">
      <header>
        <h1>Ecommerce AI Design Director</h1>
        <p className="tagline">
          Enterprise multi-agent system for world-class Shopify Plus &amp; Magento design.
        </p>
      </header>

      <section className="card">
        <h2>Backend health</h2>
        {probe.state === "loading" && <p className="muted">Checking…</p>}
        {probe.state === "ok" && (
          <ul className="kv">
            <li>
              <span>Status</span>
              <strong className="ok">{probe.data.status}</strong>
            </li>
            <li>
              <span>Service</span>
              <strong>{probe.data.service}</strong>
            </li>
            <li>
              <span>Environment</span>
              <strong>{probe.data.environment}</strong>
            </li>
          </ul>
        )}
        {probe.state === "error" && (
          <p className="error">
            Cannot reach backend: {probe.message}. Is the API running on :8000?
          </p>
        )}
      </section>

      <footer className="muted">Phase 1 — Architecture Foundation</footer>
    </main>
  );
}
