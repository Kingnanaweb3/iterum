import "./Dashboard.css";

const STATE = [
  { name: "aegis",    tier: "trusted",     score: 94, mode: "on delivery" },
  { name: "meridian", tier: "trusted",     score: 88, mode: "on delivery" },
  { name: "nadir",    tier: "blocked",     score: 16, mode: "refuse" },
];

const FEED = [
  { n: "07", who: "nadir",    out: "wrong verdict",        cls: "bad",  t: "1.84s" },
  { n: "06", who: "nadir",    out: "stale",                cls: "warn", t: "1.42s" },
  { n: "05", who: "nadir",    out: "failed after payment", cls: "bad",  t: "0.47s" },
  { n: "04", who: "nadir",    out: "delivered",            cls: "ok",   t: "2.22s" },
  { n: "03", who: "meridian", out: "delivered",            cls: "ok",   t: "2.89s" },
  { n: "02", who: "aegis",    out: "delivered",            cls: "ok",   t: "2.25s" },
];

export default function Dashboard({ repoUrl = "#", videoUrl = "#" }) {
  return (
    <section className="dash" id="moment">
      <div className="dash-inner">
        <h2 className="dash-head" data-reveal>Caught in transaction seven</h2>
        <p className="dash-sub" data-reveal style={{ "--d": "80ms" }}>
          Nadir took the payment and said a dangerous contract was safe. The
          agent already knew the truth, recorded the lie, and never bought
          from it again.
        </p>

        <div className="dash-links" data-reveal style={{ "--d": "160ms" }}>
          <a className="dash-link filled" href={videoUrl}>Watch the demo ↗</a>
          <a className="dash-link" href={repoUrl}>Read the code ↗</a>
        </div>

        <div className="panel" data-reveal="scale" style={{ "--d": "220ms" }}>
          <div className="panel-bar">
            <span className="panel-dots"><i /><i /><i /></span>
            <span>iterum · session 2 · read cold from Sibyl Memory</span>
          </div>

          <div className="panel-grid">
            <div className="panel-col">
              <p className="panel-title">What the record says</p>
              {STATE.map((s, i) => (
                <div className="decide-row" key={s.name} data-reveal="left" style={{ "--d": `${300 + i * 80}ms` }}>
                  <span className="decide-name">{s.name}</span>
                  <span className={`decide-out ${s.tier}`}>
                    {s.tier} · {s.score} · {s.mode}
                  </span>
                </div>
              ))}
              <div className="decide-pick" data-reveal style={{ "--d": "560ms" }}>
                would buy from <b>meridian</b> at 0.02 USDC<br />
                nadir is <b>blocked</b>, four times cheaper, and not an option
              </div>
            </div>

            <div className="panel-col">
              <p className="panel-title">What happened</p>
              <ul className="feed">
                {FEED.map((f, i) => (
                  <li key={f.n} data-reveal="right" style={{ "--d": `${340 + i * 70}ms` }}>
                    <span className="n">{f.n}</span>
                    <span>
                      {f.who} — <span className={`out ${f.cls}`}>{f.out}</span>
                    </span>
                    <span className="n">{f.t}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
