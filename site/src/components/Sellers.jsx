import "./Sellers.css";

const SELLERS = [
  { name: "Aegis", price: "0.05 USDC",
    note: "Careful. Rarely breaks, and costs ten times what Nadir does.",
    record: "oooooowoooo", tier: "trusted", score: "94" },
  { name: "Meridian", price: "0.02 USDC",
    note: "Fine most days. Sometimes it simply does not answer.",
    record: "oowooowoooow", tier: "trusted", score: "88" },
  { name: "Nadir", price: "0.005 USDC",
    note: "Cheapest. Took payment, then said a dangerous contract was safe.",
    record: "oxwoxx", tier: "blocked", score: "16" },
];

const CLASS = { o: "ok", w: "warn", x: "bad" };

export default function Sellers() {
  return (
    <section className="sellers" id="problem">
      <div className="sellers-inner">
        <h2 className="sellers-head" data-reveal>
          The cheapest seller lied,{" "}
          <span className="dim">and the agent believed it once</span>
        </h2>

        <div className="sellers-copy" data-reveal style={{ "--d": "90ms" }}>
          <p>
            Three sellers offer the same thing: a safety check on a token
            contract before the agent touches it. They do not cost the same,
            and they are not equally honest.
          </p>
          <p>
            Look only at the price and you pick Nadir every time. It is ten
            times cheaper than Aegis. It also takes the money and sometimes
            tells you a dangerous contract is fine.
          </p>
          <p>
            <b>A seller that goes quiet costs you a fee. A seller that lies
            costs you the thing you were protecting.</b>
          </p>
        </div>

        <div className="sellers-list">
          {SELLERS.map((s, i) => (
            <article className="seller" key={s.name} data-reveal="scale" style={{ "--d": `${i * 90}ms` }}>
              <div className="seller-top">
                <span className="seller-name">{s.name}</span>
                <span className="seller-price">{s.price}</span>
              </div>
              <p className="seller-note">{s.note}</p>
              <div className="record">
                {[...s.record].map((c, i) => (
                  <span key={i} className={`mark ${CLASS[c]}`} />
                ))}
              </div>
              <div className="seller-foot">
                <span className={`tier ${s.tier}`}>{s.tier}</span>
                <span>score {s.score}</span>
              </div>
            </article>
          ))}
        </div>

        <div className="record-key" data-reveal="fade" style={{ "--d": "280ms" }}>
          <span><i style={{ background: "#4E9A72" }} /> delivered</span>
          <span><i style={{ background: "#C79B45" }} /> late or stale</span>
          <span><i style={{ background: "#C0503F" }} /> failed or lied</span>
        </div>
      </div>
    </section>
  );
}
