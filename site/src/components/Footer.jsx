import "./Footer.css";

export default function Footer({ repoUrl = "#", videoUrl = "#" }) {
  return (
    <footer className="foot">
      <div className="foot-inner">
        <div className="foot-real">
          <div data-reveal="left">
            <h3>What is real</h3>
            <ul>
              <li>Every purchase is a live x402 payment in USDC on Base Sepolia.</li>
              <li>Sellers fail on a dice roll, not on a script.</li>
              <li>The record lives in Sibyl Memory, on disk, read by a process that saw none of it happen.</li>
            </ul>
          </div>
          <div data-reveal="right" style={{ "--d": "90ms" }}>
            <h3>What is not</h3>
            <ul>
              <li>The safety checks are made up. Iterum is not a contract scanner and does not claim to be.</li>
              <li>What is being tested here is the memory, not the security tool.</li>
            </ul>
          </div>
        </div>

        <div className="foot-cta">
          <h2 data-reveal>Trust, earned one transaction at a time</h2>
          <div className="foot-links" data-reveal style={{ "--d": "90ms" }}>
            <a className="foot-btn filled" href={repoUrl}>View the repo ↗</a>
            <a className="foot-btn ghost" href={videoUrl}>Watch the demo ↗</a>
          </div>
        </div>

        <div className="foot-meta">
          <span>Built for the Sibyl Labs Memory Hackathon · team Kingnana</span>
          <span>
            <a href="https://sibyllabs.org">Sibyl Memory</a>
            {"  ·  "}
            <a href="https://base.org">Base</a>
          </span>
        </div>

        <p className="foot-word" aria-hidden="true">Iterum</p>
      </div>
    </footer>
  );
}
