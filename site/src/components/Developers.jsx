import "./Developers.css";

const ENDPOINTS = [
  ["POST", "/v1/keys", "Get a key. No account, no email. The key is your namespace."],
  ["POST", "/v1/record", "Write down what a counterparty just did."],
  ["GET", "/v1/terms/{name}", "Ask what terms that counterparty has earned."],
  ["GET", "/v1/history/{name}", "Its whole record, and the journal it was built from."],
];

export default function Developers() {
  return (
    <section className="dev" id="developers">
      <div className="dev-inner">
        <h2 className="dev-head" data-reveal>Put it in your own agent</h2>
        <p className="dev-sub" data-reveal style={{ "--d": "80ms" }}>
          Record what a counterparty did, then ask what terms it has earned.
          Every key gets its own record. Nobody else sees yours.
        </p>

        <div className="dev-grid">
          <div className="code" data-reveal="left" style={{ "--d": "160ms" }}>
            <div className="code-bar">
              <span>python</span>
              <span>pip install -e .</span>
            </div>
            <pre>{`from iterum.graph import record_transaction, get_history
from iterum.terms import derive_terms

`}<span className="c"># after every job, write down what happened</span>{`
record_transaction(
    `}<span className="s">"acme-api"</span>{`,
    `}<span className="s">"failed_after_payment"</span>{`,
    amount_usdc=`}<span className="s">"0.005"</span>{`,
)

`}<span className="c"># in any later session, ask what it has earned</span>{`
terms = derive_terms(get_history(`}<span className="s">"acme-api"</span>{`))

`}<span className="k">if</span>{` `}<span className="k">not</span>{` terms.selectable:
    `}<span className="c"># it lied to you before. do not buy.</span>{`
    ...

`}<span className="k">print</span>{`(terms.tier, terms.payment_mode, terms.cap_usdc)
`}<span className="c"># guarded escrow 0.05</span></pre>
          </div>

          <div className="ep" data-reveal="right" style={{ "--d": "240ms" }}>
            <h3>Or over HTTP</h3>
            <ul>
              {ENDPOINTS.map(([m, route, what]) => (
                <li key={route}>
                  <span className="route"><em>{m}</em>{route}</span>
                  <span className="what">{what}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
