const assetTypes = ["Fund", "ETF", "Property Fund", "MMF", "Direct Equity", "Bond", "Other"];

const state = {
  holdings: [],
  clientType: "retail",
  asOfDate: new Date().toISOString().slice(0, 10),
  useOllama: false,
  expanded: null,
  report: "",
  downloadUrl: "",
  metrics: null,
  qualityIssues: [],
  researchUrls: "",
  researchItems: [],
  autoResearch: true,
  llmSource: "",
  status: "Load a sample portfolio or upload a portfolio file.",
  error: "",
};

const app = document.getElementById("app");

function h(tag, attrs = {}, children = []) {
  const el = document.createElement(tag);
  Object.entries(attrs).forEach(([key, value]) => {
    if (key === "class") el.className = value;
    else if (key === "text") el.textContent = value;
    else if (key === "html") el.innerHTML = value;
    else if (key.startsWith("on")) el.addEventListener(key.slice(2).toLowerCase(), value);
    else if (value !== false && value !== null && value !== undefined) el.setAttribute(key, value);
  });
  children.forEach((child) => el.appendChild(typeof child === "string" ? document.createTextNode(child) : child));
  return el;
}

function render() {
  app.innerHTML = "";
  app.appendChild(
    h("div", { class: "app-shell" }, [
      topbar(),
      h("div", { class: "workspace" }, [h("main", { class: "main" }, [controls(), researchPanel(), holdingsPanel()]), h("aside", { class: "side" }, [metricsPanel(), allocationPanel(), reportPanel(), qualityPanel()])]),
    ])
  );
}

function topbar() {
  return h("header", { class: "topbar" }, [
    h("div", { class: "brand" }, [
      h("strong", { text: "AI Client Reporting Engine" }),
      h("span", { text: "One integrated portfolio workspace for funds, ETFs, property funds, MMFs, and direct equity." }),
    ]),
    h("div", { class: "toolbar" }, [
      h("button", { text: "Load Sample", onClick: loadSample }),
      h("button", { text: "Add Holding", onClick: addHolding }),
      h("button", { class: "primary", text: "Analyze Portfolio", onClick: analyze }),
    ]),
  ]);
}

function controls() {
  const fileInput = h("input", { type: "file", accept: ".xlsx,.xls,.csv", onChange: uploadFile });
  const clientSelect = select(state.clientType, ["retail", "institutional"], (value) => {
    state.clientType = value;
    render();
  });
  const dateInput = input(state.asOfDate, (value) => {
    state.asOfDate = value;
  }, "date");
  const ollama = h("input", {
    type: "checkbox",
    ...(state.useOllama ? { checked: "checked" } : {}),
    onChange: (event) => {
      state.useOllama = event.target.checked;
    },
  });
  const autoResearch = h("input", {
    type: "checkbox",
    ...(state.autoResearch ? { checked: "checked" } : {}),
    onChange: (event) => {
      state.autoResearch = event.target.checked;
    },
  });

  return h("section", { class: "band controls-grid" }, [
    label("Client type", clientSelect),
    label("As-of date", dateInput),
    label("Upload portfolio", fileInput),
    label("Local Ollama", ollama),
    label("Auto research", autoResearch),
    h("div", { class: state.error ? "error" : "status", text: state.error || state.status }),
  ]);
}

function holdingsPanel() {
  const table = h("table", {}, [
    h("thead", {}, [
      h("tr", {}, ["", "Holding", "Type", "Identifier", "Ticker", "Market Value", "Weight", "Book Cost", "Gain/Loss", "G/L %", ""].map((text) => h("th", { class: ["Market Value", "Weight", "Book Cost", "Gain/Loss", "G/L %"].includes(text) ? "number" : "", text }))),
    ]),
    h("tbody", {}, state.holdings.flatMap((holding, index) => holdingRows(holding, index))),
  ]);

  return h("section", { class: "panel" }, [
    h("div", { class: "panel-header" }, [
      h("h2", { text: "Integrated Holdings" }),
      h("span", { class: "pill", text: `${state.holdings.length} holdings` }),
    ]),
    h("div", { class: "table-wrap" }, [table]),
  ]);
}

function researchPanel() {
  return h("section", { class: "panel" }, [
    h("div", { class: "panel-header" }, [
      h("h2", { text: "Public Research Sources" }),
      h("span", { class: "pill", text: state.autoResearch ? `auto + ${researchUrlList().length}` : `${researchUrlList().length} URLs` }),
    ]),
    h("div", { class: "research-editor" }, [
      h("textarea", {
        placeholder: "Paste public URLs or RSS feeds, one per line. Examples: central bank speeches, IMF/OECD notes, sector outlooks, fund manager commentary, ETF/fund factsheets.",
        value: state.researchUrls,
        onInput: (event) => {
          state.researchUrls = event.target.value;
        },
      }),
      h("div", { class: "hint", text: "Auto research uses curated public official/RSS sources based on the portfolio mix. Add URLs here to override or supplement." }),
      state.researchItems.length
        ? h("div", { class: "source-list" }, state.researchItems.map((item, index) => h("div", { class: "source-item" }, [h("strong", { text: `[${index + 1}] ${item.title}` }), h("span", { text: `${item.source} · ${item.published || "date not found"} · ${item.category}` }), h("p", { text: ideaPreview(item) })])))
        : h("div", { class: "hint", text: "No research sources fetched yet." }),
    ]),
  ]);
}

function holdingRows(holding, index) {
  const identifier = holding.isin || holding.sedol || holding.identifier || "";
  const row = h("tr", {}, [
    h("td", {}, [h("button", { class: "icon", title: "Expand holding", text: state.expanded === index ? "−" : "+", onClick: () => toggleExpanded(index) })]),
    h("td", { class: "name-cell" }, [input(holding.name, (value) => updateHolding(index, "name", value))]),
    h("td", {}, [select(holding.asset_type || "Fund", assetTypes, (value) => updateHolding(index, "asset_type", value))]),
    h("td", {}, [input(identifier, (value) => updateIdentifier(index, value))]),
    h("td", {}, [input(holding.ticker || "", (value) => updateHolding(index, "ticker", value.toUpperCase()))]),
    h("td", { class: "number" }, [input(holding.market_value, (value) => updateNumber(index, "market_value", value), "number")]),
    h("td", { class: "number" }, [input((weightOf(holding) * 100).toFixed(2), (value) => updateWeight(index, value), "number")]),
    h("td", { class: "number" }, [input(holding.book_cost, (value) => updateNumber(index, "book_cost", value), "number")]),
    h("td", { class: gainLossClass(holding.gain_loss) }, [input(holding.gain_loss, (value) => updateNumber(index, "gain_loss", value), "number")]),
    h("td", { class: gainLossClass(gainLossPct(holding)), text: pct(gainLossPct(holding)) }),
    h("td", {}, [h("button", { class: "icon", title: "Remove holding", text: "×", onClick: () => removeHolding(index) })]),
  ]);

  if (state.expanded !== index) return [row];

  const detail = h("tr", { class: "expanded-row" }, [
    h("td", { colspan: "11" }, [
      h("div", { class: "detail-grid" }, [
        label("ISIN", input(holding.isin || "", (value) => updateHolding(index, "isin", value.toUpperCase()))),
        label("SEDOL", input(holding.sedol || "", (value) => updateHolding(index, "sedol", value.toUpperCase()))),
        label("Currency", input(holding.currency || "GBP", (value) => updateHolding(index, "currency", value.toUpperCase()))),
        label("Report note", input(holding.note || "", (value) => updateHolding(index, "note", value))),
      ]),
    ]),
  ]);
  return [row, detail];
}

function metricsPanel() {
  const metrics = state.metrics;
  const items = metrics
    ? [
        ["Market value", money(metrics.total_market_value)],
        ["Gain/Loss", money(metrics.total_gain_loss)],
        ["Gain/Loss %", pct(metrics.total_gain_loss_pct)],
        ["Top 10 concentration", pct(metrics.concentration_top10)],
      ]
    : [
        ["Market value", money(totalMarketValue())],
        ["Gain/Loss", money(totalGainLoss())],
        ["Gain/Loss %", pct(totalGainLossPct())],
        ["Top 10 concentration", pct(topConcentration())],
      ];

  return h("section", { class: "panel" }, [
    h("div", { class: "panel-header" }, [h("h2", { text: "Portfolio Summary" }), h("span", { class: "pill", text: state.llmSource || "editable" })]),
    h("div", { class: "metric-grid" }, items.map(([labelText, value]) => h("div", { class: "metric" }, [h("span", { text: labelText }), h("strong", { text: value })]))),
  ]);
}

function allocationPanel() {
  const allocation = state.metrics?.asset_allocation || localAllocation();
  return h("section", { class: "panel" }, [
    h("div", { class: "panel-header" }, [h("h2", { text: "Asset Allocation" }), h("span", { class: "pill", text: "combined" })]),
    h("div", { class: "allocation" }, Object.entries(allocation).map(([type, value]) => h("div", { class: "allocation-row" }, [h("span", { text: type }), h("div", { class: "bar" }, [h("span", { style: `width:${Math.max(0, Math.min(100, value * 100))}%` })]), h("strong", { text: pct(value) })]))),
  ]);
}

function reportPanel() {
  const downloadControl = state.report && state.downloadUrl
    ? h("a", { class: "download-link", href: state.downloadUrl, download: `client_report_${state.asOfDate || "snapshot"}.md`, text: "Download Markdown" })
    : h("button", { text: "Download Markdown", disabled: "disabled" });
  return h("section", { class: "panel" }, [
    h("div", { class: "panel-header" }, [
      h("h2", { text: "Client Report Preview" }),
      downloadControl,
    ]),
    h("div", { class: "report", text: state.report || "Analyze the integrated portfolio to generate a client-ready report." }),
  ]);
}

function qualityPanel() {
  const issues = state.qualityIssues || [];
  return h("section", { class: "panel" }, [
    h("div", { class: "panel-header" }, [h("h2", { text: "Quality Control" })]),
    h("div", { class: "quality" }, issues.length ? issues.map((issue) => h("div", { class: "error", text: issue })) : [h("div", { class: "status", text: state.report ? "Checks passed." : "Report not generated yet." })]),
  ]);
}

function label(text, child) {
  return h("label", {}, [h("span", { text }), child]);
}

function input(value, onChange, type = "text") {
  return h("input", { type, value: value ?? "", onInput: (event) => onChange(event.target.value) });
}

function select(value, options, onChange) {
  const el = h("select", { onChange: (event) => onChange(event.target.value) }, options.map((option) => h("option", { value: option, text: option })));
  el.value = value;
  return el;
}

async function loadSample() {
  const response = await fetch("/api/sample");
  const payload = await response.json();
  state.holdings = payload.holdings;
  state.report = "";
  state.downloadUrl = "";
  state.metrics = null;
  state.error = "";
  state.status = "Sample portfolio loaded. Edit any holding, then analyze.";
  render();
}

async function uploadFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  state.status = "Reading portfolio file...";
  state.error = "";
  render();

  const response = await fetch("/api/parse-upload", { method: "POST", body: form });
  const payload = await response.json();
  if (!response.ok) {
    state.error = payload.error || "Could not read portfolio file.";
  } else {
    state.holdings = payload.holdings;
    state.report = "";
    state.downloadUrl = "";
    state.metrics = null;
    state.status = `Loaded ${payload.holdings.length} holdings from ${payload.source}.`;
  }
  render();
}

async function analyze() {
  if (!state.holdings.length) {
    state.error = "Add or upload holdings before analysis.";
    render();
    return;
  }
  state.status = "Analyzing integrated portfolio...";
  state.error = "";
  render();

  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      holdings: state.holdings,
      client_type: state.clientType,
      as_of_date: state.asOfDate,
      use_ollama: state.useOllama,
      research_urls: researchUrlList(),
      auto_research: state.autoResearch,
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    state.error = payload.error || "Could not analyze portfolio.";
  } else {
    state.report = payload.report;
    state.downloadUrl = payload.markdown_download_url || "";
    state.metrics = payload.metrics;
    state.qualityIssues = payload.quality_issues;
    state.researchItems = payload.research_items || [];
    state.llmSource = payload.llm_source;
    state.holdings = payload.holdings;
    state.status = "Analysis complete.";
  }
  render();
}

function researchUrlList() {
  return state.researchUrls
    .split("\n")
    .map((url) => url.trim())
    .filter((url) => url && !url.startsWith("#"));
}

function ideaPreview(item) {
  if (item.ideas && item.ideas.length) return item.ideas.slice(0, 2).join(" ");
  return item.excerpt || item.summary || "No extracted idea available.";
}

function addHolding() {
  state.holdings.push({
    name: "New Holding",
    isin: "",
    sedol: "",
    ticker: "",
    asset_type: "Fund",
    market_value: 0,
    book_cost: 0,
    gain_loss: 0,
    currency: "GBP",
  });
  state.expanded = state.holdings.length - 1;
  render();
}

function removeHolding(index) {
  state.holdings.splice(index, 1);
  state.metrics = null;
  render();
}

function toggleExpanded(index) {
  state.expanded = state.expanded === index ? null : index;
  render();
}

function updateHolding(index, key, value) {
  state.holdings[index][key] = value;
}

function updateNumber(index, key, value) {
  state.holdings[index][key] = value === "" ? "" : Number(value);
  state.metrics = null;
  render();
}

function updateWeight(index, value) {
  const total = totalMarketValue();
  const percentage = Number(value || 0) / 100;
  state.holdings[index].market_value = total * percentage;
  state.metrics = null;
  render();
}

function updateIdentifier(index, value) {
  if (value.length === 12 && /^[A-Z]{2}/i.test(value)) {
    state.holdings[index].isin = value.toUpperCase();
  } else {
    state.holdings[index].sedol = value.toUpperCase();
  }
}

function totalMarketValue() {
  return state.holdings.reduce((sum, holding) => sum + Number(holding.market_value || 0), 0);
}

function totalGainLoss() {
  return state.holdings.reduce((sum, holding) => sum + Number(holding.gain_loss || 0), 0);
}

function totalGainLossPct() {
  const cost = state.holdings.reduce((sum, holding) => sum + Number(holding.book_cost || 0), 0);
  return cost ? totalGainLoss() / cost : 0;
}

function weightOf(holding) {
  const total = totalMarketValue();
  return total ? Number(holding.market_value || 0) / total : 0;
}

function gainLossPct(holding) {
  const cost = Number(holding.book_cost || 0);
  return cost ? Number(holding.gain_loss || 0) / cost : 0;
}

function topConcentration() {
  return state.holdings
    .map(weightOf)
    .sort((a, b) => b - a)
    .slice(0, 10)
    .reduce((sum, value) => sum + value, 0);
}

function localAllocation() {
  const allocation = {};
  state.holdings.forEach((holding) => {
    const type = holding.asset_type || "Fund";
    allocation[type] = (allocation[type] || 0) + weightOf(holding);
  });
  return allocation;
}

function money(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function gainLossClass(value) {
  const numeric = Number(value || 0);
  return `number ${numeric < 0 ? "loss" : numeric > 0 ? "gain" : ""}`;
}

loadSample();
