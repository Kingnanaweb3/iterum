import "./Section.css";

export default function Section({ id, label, title, lead, alt = false, children }) {
  return (
    <section id={id} className={`section${alt ? " section-alt" : ""}`}>
      <div className="section-inner">
        {label && <p className="section-label">{label}</p>}
        {title && <h2 className="section-title">{title}</h2>}
        {lead && <p className="section-lead">{lead}</p>}
        {children}
      </div>
    </section>
  );
}
