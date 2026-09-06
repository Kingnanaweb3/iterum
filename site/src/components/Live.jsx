import { useCallback, useEffect, useState } from "react";
import "./Live.css";

const API = import.meta.env.VITE_API_BASE ?? "";

const TONE = {
  delivered: "ok",
  late: "warn",
  stale: "warn",
  wrong_verdict: "bad",
  failed_after_payment: "bad",
  disputed_against: "bad",
  payment_not_attempted: "warn",
};

export default function Live() {
  const [state, setState] = useState(null);
  const [feed, setFeed] = useState([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState(false);

  const load = useCallback(async () => {
    try {
      const [s, f] = await Promise.all([
        fetch(`${API}/api/state`).then((r) => r.json()),
        fetch(`${API}/api/feed?limit=8`).then((r) => r.json()),
      ]);
      setState(s);
      setFeed(f.events ?? []);
      setErr(false);
    } catch {
      setErr(true);
      setMsg("the demo backend is not reachable right now");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function run() {
    setBusy(true);
    setMsg("paying, waiting on the seller…");
    setErr(false);
    try {
      const res = await fetch(`${API}/api/run`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        setErr(true);
        setMsg(data.error ?? "that did not work");
      } else {
        const r = data.result;
        setMsg(
          r.provider
            ? `bought from ${r.provider} — recorded ${r.outcome.replace(/_/g, " ")}`
            : "no seller was allowed on current terms"
        );
        setState(data.state);
        load();
      }
    } catch {
      setErr(true);
      setMsg("the demo backend is not reachable right now");
    } finally {
      setBusy(false);
    }
  }

  const left = state?.runs_left;

  return (
    <section className="live" id="app">
      <div className="live-inner">
        <h2 className="live-head" data-reveal>Try it yourself</h2>
        <p className="live-sub" data-reveal style={{ "--d": "80ms" }}>
          One click buys a real safety check with real USDC on Base Sepolia.
          Whatever the seller does is written down, and every later decision
          reads it.
        </p>

        <div className="live-cta" data-reveal style={{ "--d": "150ms" }}>
          <button className="live-btn" onClick={run} disabled={busy}>
            {busy ? "Running…" : "Run one screening"}
          </button>
          <span className={`live-msg${err ? " err" : ""}`}>
            {msg || (left != null ? `${left} runs left in the demo wallet` : "")}
          </span>
        </div>

        <div className="live-grid">
          <div className="live-box" data-reveal="left" style={{ "--d": "220ms" }}>
            <h3>What the record says</h3>
            {state?.sellers?.length ? state.sellers.map((s) => (
              <div className="lrow" key={s.name}>
                <span className="nm">{s.name} · {s.price} USDC</span>
                <span className={`st ${s.tier}`}>{s.tier} · {s.score}</span>
                <span className="lbar">
                  {s.record.map((o, i) => (
                    <span key={i} className={`lmark ${TONE[o] ?? ""}`} />
                  ))}
                </span>
              </div>
            )) : <p className="live-empty">waiting for the backend…</p>}
          </div>

          <div className="live-box" data-reveal="right" style={{ "--d": "300ms" }}>
            <h3>What happened</h3>
            {feed.length ? (
              <ul className="lfeed">
                {feed.map((e, i) => (
                  <li key={i}>
                    <span>
                      {e.seller} — <span className={`o ${TONE[e.outcome] ?? ""}`}>
                        {e.outcome?.replace(/_/g, " ")}
                      </span>
                    </span>
                    <span className="t">{e.ts?.slice(11, 19)}</span>
                  </li>
                ))}
              </ul>
            ) : <p className="live-empty">nothing recorded yet</p>}
          </div>
        </div>
      </div>
    </section>
  );
}
