import "./Deletion.css";

function IconMemory() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="3" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </svg>
  );
}

function IconGone() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="3" />
      <path d="M8.5 8.5l7 7M15.5 8.5l-7 7" />
    </svg>
  );
}

export default function Deletion() {
  return (
    <section className="del" id="deletion">
      <div className="del-inner">
        <h2 className="del-head" data-reveal>Same code, different memory</h2>
        <p className="del-sub" data-reveal style={{ "--d": "80ms" }}>
          Nothing changes but the record. Same sellers, same prices, same
          logic. Run it once with the record and once without.
        </p>

        <article className="del-card" data-reveal="scale" style={{ "--d": "160ms" }}>
          <span className="del-icon"><IconMemory /></span>
          <h3>With memory</h3>
          <p>
            The agent reads what earlier sessions wrote. Nadir is blocked
            after taking payment and lying about a contract, so it is not an
            option however cheap it is.
          </p>
          <span className="del-out">
            buys from <span className="good">meridian</span> at 0.02 USDC
          </span>
        </article>

        <article className="del-card" data-reveal="scale" style={{ "--d": "260ms" }}>
          <span className="del-icon"><IconGone /></span>
          <h3>Memory deleted</h3>
          <p>
            Every seller is a stranger. With nothing to go on, the agent does
            the only sensible thing left and picks the cheapest one, which is
            the one that just robbed it.
          </p>
          <span className="del-out">
            buys from <span className="bad">nadir</span> at 0.005 USDC
          </span>
        </article>
      </div>
    </section>
  );
}
