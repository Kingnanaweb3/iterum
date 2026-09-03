import "./Nav.css";

const LINKS = [
  ["The problem", "#problem"],
  ["The moment", "#moment"],
  ["Deletion test", "#deletion"],
  ["Tiers", "#tiers"],
];

export default function Nav({ repoUrl = "#" }) {
  return (
    <nav className="nav">
      <a className="nav-mark" href="#top">
        <span className="nav-dot" aria-hidden="true" />
        Iterum
      </a>
      <div className="nav-links">
        {LINKS.map(([label, href]) => (
          <a key={href} href={href}>{label}</a>
        ))}
      </div>
      <a className="nav-cta" href={repoUrl}>View repo</a>
    </nav>
  );
}
