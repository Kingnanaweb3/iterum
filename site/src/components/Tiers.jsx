import "./Tiers.css";

const TIERS = [
  {
    name: "Trusted", range: "score 80 to 100", tone: "ok", on: false,
    foot: "first choice",
    rules: [
      ["Pays", "On delivery"],
      ["Cap", "0.10 USDC a check"],
      ["Retries", "Two"],
      ["Verdict", "Acted on directly"],
    ],
  },
  {
    name: "Provisional", range: "score 60 to 79", tone: "ok", on: false,
    foot: "where every seller starts",
    rules: [
      ["Pays", "On delivery"],
      ["Cap", "0.05 USDC a check"],
      ["Retries", "One"],
      ["Verdict", "Acted on directly"],
    ],
  },
  {
    name: "Guarded", range: "score 35 to 59", tone: "warn", on: true,
    foot: "has messed up at least once",
    rules: [
      ["Pays", "Money held back"],
      ["Cap", "0.05 USDC a check"],
      ["Retries", "None"],
      ["Verdict", "Needs a second opinion"],
    ],
  },
  {
    name: "Blocked", range: "score 0 to 34", tone: "bad", on: false,
    foot: "not an option at any price",
    rules: [
      ["Pays", "Nothing"],
      ["Cap", "None"],
      ["Retries", "None"],
      ["Verdict", "Never asked"],
    ],
  },
];

export default function Tiers() {
  return (
    <section className="tiers" id="tiers">
      <div className="tiers-inner">
        <h2 className="tiers-head" data-reveal>Four levels of trust</h2>
        <p className="tiers-sub" data-reveal style={{ "--d": "80ms" }}>
          Every seller sits on one rung, and the rung comes only from what it
          has done. Nothing here is set by hand.
        </p>

        <div className="tiers-grid">
          {TIERS.map((t, i) => (
            <article
              key={t.name}
              className={`tier-card${t.on ? " on" : ""}`}
              data-reveal="scale"
              style={{ "--d": `${140 + i * 90}ms` }}
            >
              <h3 className="tier-name">{t.name}</h3>
              <p className="tier-range">{t.range}</p>
              <ul className="tier-rules">
                {t.rules.map(([k, v]) => (
                  <li key={k}><b>{k}</b>{v}</li>
                ))}
              </ul>
              <p className={`tier-foot ${t.tone}`}>{t.foot}</p>
            </article>
          ))}
        </div>

        <p className="tiers-note" data-reveal="fade" style={{ "--d": "520ms" }}>
          A seller climbs back as its mistakes age out, but score alone is not
          enough. It also has to deliver twice in a row since its last bad
          record. One lucky job does not buy back trust.
        </p>
      </div>
    </section>
  );
}
