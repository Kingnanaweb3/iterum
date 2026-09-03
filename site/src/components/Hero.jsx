import "./Hero.css";

export default function Hero({ repoUrl = "#", videoUrl = "#" }) {
  return (
    <header className="hero" id="top">
      <div className="hero-wash" aria-hidden="true" />

      <div className="hero-inner">
        <h1 className="hero-title">
          <span className="hero-line1">Trust, <span className="hero-accent">earned</span> one transaction</span>
          <span className="hero-line2">
            <span>at a time</span>
            <span className="hero-lead">
              Iterum buys work from other agents and remembers how each one
              behaved. <b>It reads that record before it spends.</b>
            </span>
          </span>
        </h1>

        <div className="hero-actions">
          <a className="btn btn-primary" href={repoUrl}>View the repo</a>
          <a className="btn btn-ghost" href={videoUrl}>Watch the demo</a>
        </div>

      </div>
    </header>
  );
}
