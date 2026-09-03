import "./Scoring.css";

const GROUPS = [
  {
    title: "It did the job",
    copy: "Doing the work well is worth points, but slowly still counts for something.",
    rows: [
      ["Gave a good answer", "+8", "up"],
      ["Answered, but slowly", "+2", "up"],
    ],
  },
  {
    title: "It cost you money",
    copy: "Old news, or silence after taking the fee. Annoying and expensive, but survivable.",
    rows: [
      ["Answer was out of date", "−10", "down"],
      ["Took the money, gave nothing", "−22", "worst"],
    ],
  },
  {
    title: "It cost you the thing",
    copy: "A wrong answer is the only mistake the agent acts on. One is enough to block a seller.",
    rows: [
      ["Gave a wrong answer", "−30", "worst"],
      ["Our own payment failed", "0", "zero"],
    ],
  },
];

export default function Scoring({ videoUrl = "#" }) {
  return (
    <section className="score" id="scoring">
      <div className="score-inner">
        <h2 className="score-head" data-reveal>Not all mistakes are equal</h2>
        <p className="score-sub" data-reveal style={{ "--d": "80ms" }}>
          A seller that goes quiet costs you a fee. A seller that lies costs
          you the thing you were protecting. The scores say so.
        </p>

        <div className="score-grid">
          {GROUPS.map((g, i) => (
            <article
              className="score-card"
              key={g.title}
              data-reveal="scale"
              style={{ "--d": `${200 + i * 90}ms` }}
            >
              <h3>{g.title}</h3>
              <p>{g.copy}</p>
              <ul className="score-rows">
                {g.rows.map(([label, val, tone]) => (
                  <li key={label}>
                    <span>{label}</span>
                    <span className={`v ${tone}`}>{val}</span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
