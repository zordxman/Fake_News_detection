import { useState } from "react";

function Badge({ value }) {
  const v = value || "INCONCLUSIVE";
  return <span className={`badge ${v.toLowerCase()}`}><i />{v}</span>;
}

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyzeNews() {
    if (!text.trim()) return setError("Please enter a news article or claim first.");
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/analyze", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed.");
      setResult(data);
    } catch (e) { setError(e.message || "Could not connect to backend."); }
    finally { setLoading(false); }
  }

  const verdict = result?.final_verdict || "INCONCLUSIVE";

  return (
    <div className="app-shell">
      <div className="glow glow-a" /><div className="glow glow-b" />
      <header className="topbar">
        <div className="brand">
          <div className="logo">✓</div>
          <div><b>TruthLens</b><small>AI NEWS VERIFICATION</small></div>
        </div>
        <div className="online"><span /> AI system online</div>
      </header>

      <main className="page">
        <section className="hero">
          <div className="eyebrow">✦ SMART FACT CHECKING</div>
          <h1>Know what to trust.<br /><em>Before you share.</em></h1>
          <p>Analyze news with machine-learning classification, claim extraction, and external evidence verification in one place.</p>
        </section>

        <section className="workspace">
          <div className="card input-card">
            <div className="card-head"><div><label>STEP 01</label><h2>Paste the news</h2></div><span className="icon-box">⌁</span></div>
            <p className="muted">Paste an article, headline, or factual claim below.</p>
            <textarea value={text} onChange={e => setText(e.target.value)} placeholder="Example: Narendra Modi is the Prime Minister of India." rows={10} />
            <div className="textarea-footer"><span>{text.length} characters</span>{text && <button onClick={() => {setText("");setResult(null);setError("")}}>Clear</button>}</div>
            <button className="analyze" onClick={analyzeNews} disabled={loading}>
              {loading ? <><span className="spinner" />Analyzing evidence...</> : <>Analyze News <strong>→</strong></>}
            </button>
            {error && <div className="error">! <span>{error}</span></div>}
          </div>

          <div className="side-info">
            {[['01','ML classification','Finds patterns learned from the training dataset.'],['02','Claim extraction','Identifies factual statements worth checking.'],['03','Evidence verification','Checks claims against retrieved external sources.']].map(x => (
              <div className="step" key={x[0]}><b>{x[0]}</b><div><strong>{x[1]}</strong><p>{x[2]}</p></div></div>
            ))}
            <div className="tip">ⓘ <span>ML classification and fact checking are separate signals. A text-pattern prediction does not independently prove truth.</span></div>
          </div>
        </section>

        {loading && <div className="card loading"><span className="loader" /><div><h3>Checking your claim</h3><p>Extracting claims and searching for supporting evidence...</p></div></div>}

        {result && !loading && <section className="results">
          <div className="results-head"><div><label>STEP 02</label><h2>Analysis complete</h2></div><Badge value={verdict} /></div>
          <div className="metrics">
            <Metric title="ML classification" value={result.ml_prediction} note="Text-pattern signal" cls={String(result.ml_prediction).toLowerCase()} />
            <Metric title="Decision score" value={Number(result.decision_score).toFixed(4)} note="SVM decision boundary" />
            <Metric title="Classification strength" value={result.classification_strength} note="Based on score magnitude" />
            <Metric title="Fact check" value={verdict} note="External evidence result" cls={`verdict-${verdict.toLowerCase()}`} />
          </div>
          <div className="card fact-card">
            <div className="fact-head"><div><label>EVIDENCE REVIEW</label><h3>Fact check results</h3></div><div className="check">✓</div></div>
            <p className="result-message">{result.message}</p>
            {result.claims?.length ? <div className="claims">{result.claims.map((item,i)=><article className="claim" key={i}>
              <div className="claim-num">0{i+1}</div><div className="claim-body"><div className="claim-top"><span>CLAIM {i+1}</span><Badge value={item.verdict}/></div><p>{item.claim}</p>
              {item.evidence?.length ? <details><summary>View {item.evidence.length} evidence source{item.evidence.length>1?'s':''}</summary><div className="sources">{item.evidence.map((s,j)=><div className="source" key={j}><small>{s.source_type || 'SOURCE'}</small><b>{s.title}</b><span>{s.publisher || s.publisher_url}</span></div>)}</div></details> : null}</div>
            </article>)}</div> : <div className="empty">⌁ <span>No verifiable claims were found.</span></div>}
          </div>
          <div className="disclaimer"><b>i</b><div><strong>How to read this result</strong><p>The ML classification is based on text patterns learned from the training dataset. The fact-check verdict is a separate evidence-based result.</p></div></div>
        </section>}
      </main>
      <footer>TruthLens <span>•</span> AI-powered news analysis</footer>
    </div>
  );
}

function Metric({title,value,note,cls=''}) { return <div className="metric"><div><span>{title}</span><i>◈</i></div><strong className={cls}>{value}</strong><small>{note}</small></div>; }
