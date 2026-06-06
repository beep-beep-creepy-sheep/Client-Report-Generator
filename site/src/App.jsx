import { useEffect, useMemo, useState } from "react";

const assetTypes = ["Fund", "ETF", "Property Fund", "MMF", "Direct Equity", "Bond", "Other"];

const defaultSources = [
  {
    title: "Federal Reserve Monetary Policy Releases",
    source: "federalreserve.gov",
    category: "Monetary Policy",
    idea: "Policy-rate evidence helps interpret MMF income, reinvestment risk, and opportunity cost.",
  },
  {
    title: "Bank of England News and Publications",
    source: "bankofengland.co.uk",
    category: "Monetary Policy",
    idea: "UK rate and inflation commentary is relevant for sterling liquidity and property fund assumptions.",
  },
  {
    title: "BBC Business RSS",
    source: "feeds.bbci.co.uk/news/business/rss.xml",
    category: "Market News",
    idea: "Business headlines provide broad market context without paid research APIs.",
  },
  {
    title: "Yahoo Finance News",
    source: "finance.yahoo.com/news",
    category: "Market News",
    idea: "Free market news can supplement public institutional sources for equity and ETF context.",
  },
];

const emptyHolding = {
  name: "New Holding",
  isin: "",
  sedol: "",
  ticker: "",
  asset_type: "Fund",
  market_value: 0,
  book_cost: 0,
  gain_loss: 0,
  gain_loss_pct: 0,
  currency: "GBP",
};

function App() {
  const [holdings, setHoldings] = useState([]);
  const [clientType, setClientType] = useState("retail");
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().slice(0, 10));
  const [expanded, setExpanded] = useState(null);
  const [autoResearch, setAutoResearch] = useState(true);
  const [researchUrls, setResearchUrls] = useState("");
  const [report, setReport] = useState("");
  const [qualityIssues, setQualityIssues] = useState([]);
  const [status, setStatus] = useState("Load a sample portfolio or upload a CSV file. XLSX upload is available in local Python mode.");
  const [error, setError] = useState("");

  useEffect(() => {
    loadSample();
  }, []);

  const metrics = useMemo(() => computeMetrics(holdings), [holdings]);
  const researchItems = useMemo(() => buildResearchItems(autoResearch, researchUrls), [autoResearch, researchUrls]);
  const downloadUrl = useMemo(() => {
    if (!report) return "";
    return URL.createObjectURL(new Blob([report], { type: "text/markdown;charset=utf-8" }));
  }, [report]);

  async function loadSample() {
    const response = await fetch("/data/sample_portfolio.json");
    const sample = await response.json();
    setHoldings(normalizeRows(sample));
    setReport("");
    setQualityIssues([]);
    setError("");
    setStatus("Sample portfolio loaded. Edit any holding, then analyze.");
  }

  function addHolding() {
    setHoldings((current) => [...current, { ...emptyHolding }]);
    setExpanded(holdings.length);
    setReport("");
  }

  function updateHolding(index, key, value) {
    setHoldings((current) =>
      current.map((holding, rowIndex) => {
        if (rowIndex !== index) return holding;
        const next = { ...holding, [key]: value };
        if (["market_value", "book_cost", "gain_loss"].includes(key)) {
          next[key] = toNumber(value);
          next.gain_loss_pct = next.book_cost ? next.gain_loss / next.book_cost : 0;
        }
        return next;
      })
    );
    setReport("");
  }

  function updateIdentifier(index, value) {
    setHoldings((current) =>
      current.map((holding, rowIndex) => {
        if (rowIndex !== index) return holding;
        if (/^[A-Z]{2}/i.test(value)) return { ...holding, isin: value.toUpperCase(), sedol: "" };
        return { ...holding, sedol: value.toUpperCase(), isin: "" };
      })
    );
  }

  function updateWeight(index, rawWeight) {
    const value = Math.max(0, toNumber(rawWeight) / 100);
    const total = totalMarketValue(holdings);
    const nextValue = total * value;
    updateHolding(index, "market_value", Number.isFinite(nextValue) ? nextValue : 0);
  }

  function removeHolding(index) {
    setHoldings((current) => current.filter((_, rowIndex) => rowIndex !== index));
    setExpanded(null);
    setReport("");
  }

  async function uploadFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const rows = await readPortfolioFile(file);
      setHoldings(normalizeRows(rows));
      setReport("");
      setQualityIssues([]);
      setError("");
      setStatus(`Loaded ${rows.length} holdings from ${file.name}. Live demo parsing is browser-only.`);
    } catch (uploadError) {
      setError(uploadError.message || "Could not read portfolio file.");
    }
  }

  function analyze() {
    if (!holdings.length || metrics.total_market_value <= 0) {
      setError("Add at least one holding with positive market value.");
      return;
    }
    const generated = buildReport(metrics, holdings, clientType, asOfDate, researchItems);
    const issues = validateReport(generated, metrics);
    setReport(generated);
    setQualityIssues(issues);
    setError("");
    setStatus("Report generated in browser demo mode. Local Python mode runs full research fetching and optional Ollama.");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <strong>AI Client Reporting Engine</strong>
          <span>Interactive Vercel trial for funds, ETFs, property funds, MMFs, and direct equity.</span>
        </div>
        <div className="toolbar">
          <button onClick={loadSample}>Load Sample</button>
          <button onClick={addHolding}>Add Holding</button>
          <button className="primary" onClick={analyze}>Analyze Portfolio</button>
        </div>
      </header>

      <div className="demo-notice">
        Public trial mode. Do not upload private client data. Live web research, yfinance, PDF export, and Ollama run in the local Python app.
      </div>

      <div className="workspace">
        <main className="main">
          <section className="band controls-grid">
            <label>
              <span>Client type</span>
              <select value={clientType} onChange={(event) => setClientType(event.target.value)}>
                <option value="retail">retail</option>
                <option value="institutional">institutional</option>
              </select>
            </label>
            <label>
              <span>As-of date</span>
              <input type="date" value={asOfDate} onChange={(event) => setAsOfDate(event.target.value)} />
            </label>
            <label>
              <span>Upload portfolio</span>
              <input type="file" accept=".csv" onChange={uploadFile} />
            </label>
            <label className="checkbox-label">
              <span>Auto research</span>
              <input type="checkbox" checked={autoResearch} onChange={(event) => setAutoResearch(event.target.checked)} />
            </label>
            <div className={error ? "error" : "status"}>{error || status}</div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Public Research Sources</h2>
              <span className="pill">{autoResearch ? `auto + ${researchUrlList(researchUrls).length}` : `${researchUrlList(researchUrls).length} URLs`}</span>
            </div>
            <div className="research-editor">
              <textarea
                placeholder="Paste public URLs or RSS feeds, one per line. Vercel trial records them as context; local Python mode fetches and extracts source text."
                value={researchUrls}
                onChange={(event) => setResearchUrls(event.target.value)}
              />
              <div className="source-list">
                {researchItems.map((item, index) => (
                  <div className="source-item" key={`${item.source}-${index}`}>
                    <strong>[{index + 1}] {item.title}</strong>
                    <span>{item.source} · {item.category}</span>
                    <p>{item.idea}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Integrated Holdings</h2>
              <span className="pill">{holdings.length} holdings</span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    {["", "Holding", "Type", "Identifier", "Ticker", "Market Value", "Weight", "Book Cost", "Gain/Loss", "G/L %", ""].map((header) => (
                      <th key={header} className={["Market Value", "Weight", "Book Cost", "Gain/Loss", "G/L %"].includes(header) ? "number" : ""}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {holdings.flatMap((holding, index) => [
                    <tr key={`${index}-main`}>
                      <td><button className="icon" onClick={() => setExpanded(expanded === index ? null : index)}>{expanded === index ? "-" : "+"}</button></td>
                      <td className="name-cell"><input value={holding.name} onChange={(event) => updateHolding(index, "name", event.target.value)} /></td>
                      <td><select value={holding.asset_type} onChange={(event) => updateHolding(index, "asset_type", event.target.value)}>{assetTypes.map((type) => <option key={type}>{type}</option>)}</select></td>
                      <td><input value={holding.isin || holding.sedol || ""} onChange={(event) => updateIdentifier(index, event.target.value)} /></td>
                      <td><input value={holding.ticker || ""} onChange={(event) => updateHolding(index, "ticker", event.target.value.toUpperCase())} /></td>
                      <td className="number"><input type="number" value={holding.market_value} onChange={(event) => updateHolding(index, "market_value", event.target.value)} /></td>
                      <td className="number"><input type="number" value={(weightOf(holding, holdings) * 100).toFixed(2)} onChange={(event) => updateWeight(index, event.target.value)} /></td>
                      <td className="number"><input type="number" value={holding.book_cost} onChange={(event) => updateHolding(index, "book_cost", event.target.value)} /></td>
                      <td className={gainLossClass(holding.gain_loss)}><input type="number" value={holding.gain_loss} onChange={(event) => updateHolding(index, "gain_loss", event.target.value)} /></td>
                      <td className={gainLossClass(gainLossPct(holding))}>{pct(gainLossPct(holding))}</td>
                      <td><button className="icon" onClick={() => removeHolding(index)}>x</button></td>
                    </tr>,
                    expanded === index ? (
                      <tr className="expanded-row" key={`${index}-detail`}>
                        <td colSpan="11">
                          <div className="detail-grid">
                            <label><span>ISIN</span><input value={holding.isin || ""} onChange={(event) => updateHolding(index, "isin", event.target.value.toUpperCase())} /></label>
                            <label><span>SEDOL</span><input value={holding.sedol || ""} onChange={(event) => updateHolding(index, "sedol", event.target.value.toUpperCase())} /></label>
                            <label><span>Currency</span><input value={holding.currency || "GBP"} onChange={(event) => updateHolding(index, "currency", event.target.value.toUpperCase())} /></label>
                            <label><span>Report note</span><input value={holding.note || ""} onChange={(event) => updateHolding(index, "note", event.target.value)} /></label>
                          </div>
                        </td>
                      </tr>
                    ) : null,
                  ])}
                </tbody>
              </table>
            </div>
          </section>
        </main>

        <aside className="side">
          <SummaryPanel metrics={metrics} />
          <AllocationPanel allocation={metrics.asset_allocation} />
          <ReportPanel report={report} downloadUrl={downloadUrl} asOfDate={asOfDate} />
          <QualityPanel issues={qualityIssues} report={report} />
        </aside>
      </div>
    </div>
  );
}

function SummaryPanel({ metrics }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Portfolio Summary</h2><span className="pill">browser demo</span></div>
      <div className="metric-grid">
        <div className="metric"><span>Market value</span><strong>{money(metrics.total_market_value)}</strong></div>
        <div className="metric"><span>Gain/Loss</span><strong>{money(metrics.total_gain_loss)}</strong></div>
        <div className="metric"><span>Gain/Loss %</span><strong>{pct(metrics.total_gain_loss_pct)}</strong></div>
        <div className="metric"><span>Top 10 concentration</span><strong>{pct(metrics.concentration_top10)}</strong></div>
      </div>
    </section>
  );
}

function AllocationPanel({ allocation }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Asset Allocation</h2><span className="pill">combined</span></div>
      <div className="allocation">
        {Object.entries(allocation).map(([type, value]) => (
          <div className="allocation-row" key={type}>
            <span>{type}</span>
            <div className="bar"><span style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }} /></div>
            <strong>{pct(value)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function ReportPanel({ report, downloadUrl, asOfDate }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Client Report Preview</h2>
        {report ? <a className="download-link" href={downloadUrl} download={`client_report_${asOfDate}.md`}>Download Markdown</a> : <button disabled>Download Markdown</button>}
      </div>
      <div className="report">{report || "Analyze the integrated portfolio to generate a client-ready report."}</div>
    </section>
  );
}

function QualityPanel({ issues, report }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Quality Control</h2></div>
      <div className="quality">
        {issues.length ? issues.map((issue) => <div className="error" key={issue}>{issue}</div>) : <div className="status">{report ? "Checks passed." : "Report not generated yet."}</div>}
      </div>
    </section>
  );
}

async function readPortfolioFile(file) {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    throw new Error("The public Vercel trial accepts CSV files only. Use local Python mode for XLS/XLSX uploads.");
  }
  const text = await file.text();
  return parseCsv(text);
}

function parseCsv(text) {
  const rows = text.trim().split(/\r?\n/).filter(Boolean).map((line) => line.split(",").map((cell) => cell.trim()));
  const headers = rows.shift()?.map(cleanColumn) || [];
  return rows.map((row) => Object.fromEntries(headers.map((header, index) => [header, row[index] || ""])));
}

function normalizeRows(rows) {
  return rows.map((row) => {
    const normalized = {};
    Object.entries(row).forEach(([key, value]) => {
      normalized[cleanColumn(key)] = value;
    });
    const marketValue = toNumber(pick(normalized, ["market_value", "market value", "value", "valuation", "mv"]));
    const bookCost = toNumber(pick(normalized, ["book_cost", "book cost", "cost", "cost_basis"])) || marketValue;
    const gainLoss = toNumber(pick(normalized, ["gain_loss", "gain/loss", "gain loss", "pnl"])) || marketValue - bookCost;
    return {
      name: String(pick(normalized, ["name", "holding", "security", "fund_name", "description"]) || "Unnamed holding").trim(),
      isin: String(pick(normalized, ["isin", "isin_code"]) || "").trim().toUpperCase(),
      sedol: String(pick(normalized, ["sedol", "sedol_code"]) || "").trim().toUpperCase(),
      ticker: String(pick(normalized, ["ticker", "symbol", "yf_ticker"]) || "").trim().toUpperCase(),
      asset_type: normalizeAssetType(String(pick(normalized, ["asset_type", "asset class", "asset_class", "type", "instrument_type"]) || "Fund")),
      market_value: marketValue,
      book_cost: bookCost,
      gain_loss: gainLoss,
      gain_loss_pct: bookCost ? gainLoss / bookCost : 0,
      currency: String(pick(normalized, ["currency", "ccy"]) || "GBP").trim().toUpperCase(),
    };
  }).filter((holding) => holding.market_value !== 0);
}

function computeMetrics(holdings) {
  const total = totalMarketValue(holdings);
  const totalBookCost = holdings.reduce((sum, holding) => sum + toNumber(holding.book_cost), 0);
  const totalGainLoss = holdings.reduce((sum, holding) => sum + toNumber(holding.gain_loss), 0);
  const allocation = {};
  holdings.forEach((holding) => {
    allocation[holding.asset_type] = (allocation[holding.asset_type] || 0) + (total ? holding.market_value / total : 0);
  });
  const sorted = [...holdings].sort((a, b) => b.market_value - a.market_value);
  const fundWeight = ["Fund", "ETF", "Property Fund"].reduce((sum, type) => sum + (allocation[type] || 0), 0);
  return {
    total_market_value: total,
    total_book_cost: totalBookCost,
    total_gain_loss: totalGainLoss,
    total_gain_loss_pct: totalBookCost ? totalGainLoss / totalBookCost : 0,
    asset_allocation: allocation,
    concentration_top10: sorted.slice(0, 10).reduce((sum, holding) => sum + weightOf(holding, holdings), 0),
    fund_weight: fundWeight,
    mmf_weight: allocation.MMF || 0,
    property_fund_weight: allocation["Property Fund"] || 0,
    direct_equity_weight: allocation["Direct Equity"] || 0,
    top_positions: sorted.slice(0, 10),
    winners: [...holdings].filter((holding) => holding.gain_loss > 0).sort((a, b) => b.gain_loss - a.gain_loss),
    losers: [...holdings].filter((holding) => holding.gain_loss < 0).sort((a, b) => a.gain_loss - b.gain_loss),
  };
}

function buildResearchItems(autoResearch, rawUrls) {
  const custom = researchUrlList(rawUrls).map((url) => ({
    title: url,
    source: url.replace(/^https?:\/\//, ""),
    category: "User Source",
    idea: "User-supplied public source recorded for local-mode fetching and report context.",
  }));
  return [...(autoResearch ? defaultSources : []), ...custom];
}

function buildReport(metrics, holdings, clientType, asOfDate, researchItems) {
  const largest = metrics.top_positions[0];
  const winners = metrics.winners.slice(0, 3).map((holding) => `${holding.name} (${money(holding.gain_loss)})`).join(", ") || "no positive contributors";
  const losers = metrics.losers.slice(0, 3).map((holding) => `${holding.name} (${money(holding.gain_loss)})`).join(", ") || "no negative contributors";
  const allocation = Object.entries(metrics.asset_allocation).map(([type, value]) => `${type}: ${pct(value)}`).join("; ");
  const title = clientType === "institutional" ? "Institutional Portfolio Snapshot Report" : "Client Portfolio Snapshot Report";
  return `# ${title}

**Report date:** ${asOfDate}
**Analytical basis:** Browser demo calculation using editable portfolio snapshot. Local Python mode adds live public-source fetching, yfinance support, optional Ollama, and PDF export.

## Performance Summary
As of ${asOfDate}, the portfolio was valued at ${money(metrics.total_market_value)} across ${holdings.length} holdings, with unrealized gain/loss of ${money(metrics.total_gain_loss)}, or ${pct(metrics.total_gain_loss_pct)} on book cost. The portfolio structure is led by pooled vehicles: funds, ETFs, and property funds represent ${pct(metrics.fund_weight)} of value, while MMF/cash-like exposure is ${pct(metrics.mmf_weight)} and direct equity exposure is ${pct(metrics.direct_equity_weight)}.

## Methodology and Data Basis
This public trial performs client-side calculations only. It uses market value, book cost, gain/loss, asset type, ISIN, SEDOL, and ticker values entered in the table. Private portfolio data should be processed in local mode rather than on the public demo.

## Allocation Analysis
Asset allocation is ${allocation}. ${largest ? `The largest holding is ${largest.name} at ${pct(weightOf(largest, holdings))}.` : ""} This mix makes allocation, manager selection, vehicle liquidity, and implementation discipline more important than isolated security commentary.

## Attribution Analysis
Leading positive contributors are ${winners}. Principal detractors are ${losers}. The report reads gain/loss at both holding and asset-type level because a positive total result can still conceal weak sub-portfolios or liquidity-constrained detractors.

## Research Context
${researchItems.slice(0, 4).map((item, index) => `${item.source} contributes ${item.category.toLowerCase()} context: ${item.idea} [${index + 1}]`).join(" ")}

## Evidence Synthesis
The research context becomes useful only when read through measured exposure. With ${pct(metrics.fund_weight)} in pooled vehicles, research conclusions primarily affect manager, vehicle, and allocation review. With ${pct(metrics.mmf_weight)} in MMF/cash-like holdings, policy and liquidity evidence affects expected income, reinvestment risk, and opportunity cost.

## Liquidity and Implementation Risk
Top-ten concentration is ${pct(metrics.concentration_top10)}. Property fund exposure of ${pct(metrics.property_fund_weight)} requires review of valuation frequency, redemption terms, and dealing constraints. MMF exposure of ${pct(metrics.mmf_weight)} supports liquidity but creates reinvestment and opportunity-cost questions if policy rates change.

## Portfolio Implications
The practical conclusion is that the portfolio should be governed through allocation decisions, not isolated narrative. Rebalances should be justified by the interaction between measured portfolio facts, liquidity terms, and cited public evidence.

## Outlook Commentary
The next review should reconcile the largest gain/loss contributors with concentration and liquidity before approving any rebalance. Local Python mode should be used for real client reporting because it keeps sensitive data offline and runs the complete reporting pipeline.

## References
${researchItems.map((item, index) => `${index + 1}. ${item.source}, "${item.title}," public demo source.`).join("\n")}
`;
}

function validateReport(report, metrics) {
  const issues = [];
  ["Performance Summary", "Methodology and Data Basis", "Allocation Analysis", "Attribution Analysis", "Evidence Synthesis", "Liquidity and Implementation Risk", "Portfolio Implications", "Outlook Commentary"].forEach((section) => {
    if (!report.includes(section)) issues.push(`Missing section: ${section}.`);
  });
  if (!report.includes(pct(metrics.total_gain_loss_pct)) && !report.includes(money(metrics.total_gain_loss))) {
    issues.push("Report does not reference calculated portfolio metrics.");
  }
  return issues;
}

function totalMarketValue(holdings) {
  return holdings.reduce((sum, holding) => sum + toNumber(holding.market_value), 0);
}

function weightOf(holding, holdings) {
  const total = totalMarketValue(holdings);
  return total ? toNumber(holding.market_value) / total : 0;
}

function gainLossPct(holding) {
  return holding.book_cost ? holding.gain_loss / holding.book_cost : 0;
}

function gainLossClass(value) {
  return value < 0 ? "number loss" : value > 0 ? "number gain" : "number";
}

function researchUrlList(rawUrls) {
  return rawUrls.split(/\r?\n/).map((url) => url.trim()).filter(Boolean);
}

function normalizeAssetType(value) {
  const cleaned = value.trim().toLowerCase();
  const aliases = {
    "direct equity": "Direct Equity",
    equity: "Direct Equity",
    stock: "Direct Equity",
    etf: "ETF",
    fund: "Fund",
    "mutual fund": "Fund",
    "property fund": "Property Fund",
    "real estate fund": "Property Fund",
    mmf: "MMF",
    cash: "MMF",
    "money market": "MMF",
  };
  return aliases[cleaned] || (value.trim() ? value.trim().replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Fund");
}

function cleanColumn(value) {
  return String(value).trim().toLowerCase().replaceAll("-", "_");
}

function pick(row, keys) {
  for (const key of keys) {
    if (row[key] !== undefined && row[key] !== "") return row[key];
  }
  return "";
}

function toNumber(value) {
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  const cleaned = String(value || "").replace(/[£$€,]/g, "").replace("%", "").trim();
  if (!cleaned) return 0;
  if (cleaned.startsWith("(") && cleaned.endsWith(")")) return -Number(cleaned.slice(1, -1));
  return Number(cleaned) || 0;
}

function money(value) {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 }).format(value || 0);
}

function pct(value) {
  return `${((value || 0) * 100).toFixed(1)}%`;
}

export default App;
