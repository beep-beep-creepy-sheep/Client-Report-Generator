const layers = [
  { title: "Local Python Workspace", nodes: ["Excel/CSV upload", "portfolio_upload.py", "snapshot.py", "web_sources.py", "report_builder.py"] },
  { title: "Report Generation", nodes: ["Deterministic fallback", "Optional Ollama", "quality.py", "Markdown/PDF export"] },
  { title: "Public Website", nodes: ["Vite React", "Static JSON demo", "No backend calls", "Vercel dist output"] },
];

function ArchitectureDiagram() {
  return (
    <div className="architecture-wrap">
      <div className="architecture-diagram">{layers.map((layer) => <section className="architecture-layer" key={layer.title}><h3>{layer.title}</h3><div>{layer.nodes.map((node) => <span key={node}>{node}</span>)}</div></section>)}</div>
      <div className="architecture-notes"><h3>Boundary that matters</h3><p>The static website is a public showcase. The real portfolio analysis engine remains local because holdings, cost basis, gain/loss, and client reporting context are sensitive.</p><p>Vercel serves the React site from static files. It does not run <code>/api/analyze</code>, fetch private sources, or call Ollama.</p></div>
    </div>
  );
}

export default ArchitectureDiagram;
