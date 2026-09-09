import { useEffect, useState } from "react";
import "./Stats.css";

const API = import.meta.env.VITE_API_BASE ?? "";

export default function Stats() {
  const [s, setS] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/stats`).then(r => r.json()).then(setS).catch(() => {});
  }, []);

  if (!s || !s.transactions) return null;

  return (
    <section className="stats">
      <div className="stats-inner">
        <p className="stats-title" data-reveal="fade">Counted from the journal, live</p>
        <div className="stats-grid">
          <article className="stat" data-reveal="scale" style={{ "--d": "0ms" }}>
            <div className="stat-n hi">{s.override_pct}%</div>
            <p className="stat-l">of purchases went to a seller that was not the cheapest</p>
          </article>
          <article className="stat" data-reveal="scale" style={{ "--d": "80ms" }}>
            <div className="stat-n">{s.transactions}</div>
            <p className="stat-l">real payments settled on Base Sepolia</p>
          </article>
          <article className="stat" data-reveal="scale" style={{ "--d": "160ms" }}>
            <div className="stat-n">{s.lies}</div>
            <p className="stat-l">lies caught and recorded against the seller</p>
          </article>
          <article className="stat" data-reveal="scale" style={{ "--d": "240ms" }}>
            <div className="stat-n">{s.spent_usdc}</div>
            <p className="stat-l">USDC spent, {s.wasted_pct}% of it on nothing usable</p>
          </article>
        </div>
        <p className="stats-note" data-reveal="fade" style={{ "--d": "320ms" }}>
          Nothing here is stored. Every number is counted from an append-only journal.
        </p>
      </div>
    </section>
  );
}
