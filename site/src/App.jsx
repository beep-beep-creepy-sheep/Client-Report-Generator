import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BarChart3, BookOpenCheck, Database, Download, FileSpreadsheet, Github, LineChart, LockKeyhole, Network, ShieldCheck, Sparkles } from "lucide-react";
import MetricCard from "./components/MetricCard.jsx";
import HoldingsTable from "./components/HoldingsTable.jsx";
import AllocationChart from "./components/AllocationChart.jsx";
import WorkflowStep from "./components/WorkflowStep.jsx";
import ReportPreview from "./components/ReportPreview.jsx";
import SourceList from "./components/SourceList.jsx";
import QualityChecks from "./components/QualityChecks.jsx";
import ArchitectureDiagram from "./components/ArchitectureDiagram.jsx";

const dataFiles = {
  portfolio: "/data/sample_portfolio.json",
  metrics: "/data/sample_metrics.json",
  report: "/data/sample_report.json",
  workflow: "/data/workflow_steps.json",
  checks: "/data/quality_checks.json",
  sources: "/data/research_sources.json",
};

const capabilities = [
  ["Portfolio analytics", "Snapshot metrics, allocation, attribution, concentration, and risk flags.", BarChart3],
  ["Fund-heavy upload", "Designed for portfolios dominated by funds, ETFs, property funds, and MMFs.", FileSpreadsheet],
  ["ISIN/SEDOL/ticker support", "Identifiers support clean repeatable reporting.", Database],
  ["Public research ingestion", "Local mode reads public pages and RSS feeds without paid research APIs.", Network],
  ["Metric-aware commentary", "Narrative is anchored to gain/loss, weights, and exposure figures.", BookOpenCheck],
  ["Local LLM optional", "Deterministic fallback works offline; Ollama can be enabled locally.", Sparkles],
  ["Markdown/PDF export", "Reports can be exported from the Python-backed local workspace.", Download],
  ["Quality controls", "Checks required sections, vague language, and missing metric references.", ShieldCheck],
];

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadData() {
      try {
        const entries = await Promise.all(
          Object.entries(dataFiles).map(async ([key, url]) => {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Could not load ${url}`);
            return [key, await response.json()];
          })
        );
        if (!cancelled) setData(Object.fromEntries(entries));
      } catch (loadError) {
        if (!cancelled) setError(loadError.message || "Static demo data could not be loaded.");
      }
    }
    loadData();
    return () => {
      cancelled = true;
    };
  }, []);

  const topHoldings = useMemo(() => data?.portfolio?.slice(0, 5) || [], [data]);

  if (error) {
    return (
      <main className="load-state" role="alert">
        <h1>AI Client Reporting Engine</h1>
        <p>{error}</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="load-state">
        <h1>AI Client Reporting Engine</h1>
        <p>Loading static demonstration workspace...</p>
      </main>
    );
  }

  return (
    <div className="site-shell">
      <nav className="top-nav" aria-label="Primary navigation">
        <a className="brand-mark" href="#overview">
          <LineChart size={22} />
          <span>AI Client Reporting Engine</span>
        </a>
        <div className="nav-links">
          <a href="#workflow">Workflow</a>
          <a href="#dashboard">Dashboard</a>
          <a href="#report">Report</a>
          <a href="#architecture">Architecture</a>
          <a href="#run">Run</a>
        </div>
      </nav>

      <main>
        <section id="overview" className="overview-section section-pad">
          <div className="overview-copy">
            <p className="eyebrow">Offline-first wealth reporting workspace</p>
            <h1>AI Client Reporting Engine</h1>
            <p className="tagline">Offline-first portfolio reporting workspace for wealth management teams.</p>
            <p className="intro">
              A Python reporting engine and local workspace that combines portfolio analytics, uploaded fund-heavy holdings,
              public research ingestion, deterministic report generation, optional local Ollama, quality checks, and exportable reports.
            </p>
            <div className="cta-row">
              <a className="button primary" href="#workflow">View Demo Workflow <ArrowRight size={17} /></a>
              <a className="button" href="#report">View Sample Report</a>
              <a className="button ghost" href="https://github.com/beep-beep-creepy-sheep/Client-Report-Generator" target="_blank" rel="noreferrer"><Github size={17} /> View GitHub Repo</a>
              <a className="button ghost" href="#run">Run Locally</a>
            </div>
          </div>
          <div className="product-frame">
            <div className="frame-header">
              <span>Client Portfolio Snapshot</span>
              <strong>{data.metrics.as_of_date}</strong>
            </div>
            <div className="frame-metrics">
              <MetricCard label="Market Value" value={money(data.metrics.total_market_value)} tone="blue" />
              <MetricCard label="Gain/Loss" value={money(data.metrics.total_gain_loss)} tone="green" />
              <MetricCard label="Fund/ETF/Property" value={percent(data.metrics.fund_weight)} tone="gold" />
            </div>
            <AllocationChart allocation={data.metrics.asset_allocation} compact />
          </div>
        </section>

        <section className="disclaimer-bar">
          <LockKeyhole size={18} />
          <span>Static public demo only. Do not enter client data here. Private analysis runs in the local Python app. Not financial advice.</span>
        </section>

        <section className="section-pad">
          <div className="section-heading">
            <p className="eyebrow">Capability map</p>
            <h2>What the engine actually does</h2>
          </div>
          <div className="capability-grid">
            {capabilities.map(([title, body, Icon]) => (
              <article className="capability-card" key={title}>
                <Icon size={22} />
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="workflow" className="section-pad">
          <div className="section-heading">
            <p className="eyebrow">Product workflow</p>
            <h2>From holdings file to client-ready report</h2>
          </div>
          <div className="workflow-list">
            {data.workflow.map((step, index) => <WorkflowStep key={step.title} index={index + 1} step={step} />)}
          </div>
        </section>

        <section id="dashboard" className="section-pad dashboard-section">
          <div className="section-heading">
            <p className="eyebrow">Static demo dashboard</p>
            <h2>Fund-heavy portfolio snapshot</h2>
            <p>This dashboard uses local JSON only. It mirrors the workflow but does not call the Python API on Vercel.</p>
          </div>
          <div className="dashboard-grid">
            <MetricCard label="Total Market Value" value={money(data.metrics.total_market_value)} detail="Uploaded valuation basis" />
            <MetricCard label="Gain/Loss on Cost" value={percent(data.metrics.total_gain_loss_pct)} detail={money(data.metrics.total_gain_loss)} tone="green" />
            <MetricCard label="Holdings" value={String(data.metrics.holdings_count)} detail="Funds, ETF, MMF, property, direct equity" tone="blue" />
            <MetricCard label="Top 3 Concentration" value={percent(data.metrics.concentration_top3)} detail="Demo concentration signal" tone="amber" />
          </div>
          <div className="two-column">
            <div className="panel"><div className="panel-title"><h3>Holdings</h3><span>{data.portfolio.length} instruments</span></div><HoldingsTable holdings={data.portfolio} /></div>
            <div className="panel"><div className="panel-title"><h3>Allocation</h3><span>Market-value weighted</span></div><AllocationChart allocation={data.metrics.asset_allocation} /></div>
          </div>
          <div className="two-column slim">
            <div className="panel">
              <div className="panel-title"><h3>Top Holdings</h3><span>By market value</span></div>
              <ol className="ranked-list">{topHoldings.map((holding) => <li key={holding.name}><span>{holding.name}</span><strong>{percent(holding.weight)}</strong></li>)}</ol>
            </div>
            <QualityChecks checks={data.checks} flags={data.metrics.risk_flags} />
          </div>
          <SourceList sources={data.sources} />
        </section>

        <section id="report" className="section-pad">
          <div className="section-heading">
            <p className="eyebrow">Sample output</p>
            <h2>Client-report style narrative</h2>
            <p>The full local app generates reports from uploaded portfolios. This page renders a representative static sample.</p>
          </div>
          <ReportPreview report={data.report} />
        </section>

        <section id="architecture" className="section-pad">
          <div className="section-heading"><p className="eyebrow">Technical architecture</p><h2>Python engine plus static public website</h2></div>
          <ArchitectureDiagram />
        </section>

        <section id="run" className="section-pad run-section">
          <div className="section-heading"><p className="eyebrow">Deployment and local mode</p><h2>Use the right surface for the right job</h2></div>
          <div className="run-grid">
            <CommandBlock title="Original Python local app" lines={["pip install -r requirements.txt", "python3 web_app/server.py"]} description="Use this for private portfolio data, Excel uploads, local research fetching, Ollama, and Markdown/PDF export." />
            <CommandBlock title="Static React/Vite website" lines={["cd site", "npm install", "npm run dev", "npm run build"]} description="Use this for the public portfolio website. It reads static demo JSON and is safe to deploy without the Python backend." />
            <CommandBlock title="Vercel settings" lines={["Framework preset: Vite", "Root directory: site", "Build command: npm run build", "Output directory: dist"]} description="Deploy the static site, then paste the URL into the GitHub repository About/Website field." />
          </div>
        </section>
      </main>
    </div>
  );
}

function CommandBlock({ title, lines, description }) {
  return <article className="command-block"><h3>{title}</h3><p>{description}</p><pre>{lines.join("\n")}</pre></article>;
}

function money(value) {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 }).format(value);
}

function percent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

export default App;
