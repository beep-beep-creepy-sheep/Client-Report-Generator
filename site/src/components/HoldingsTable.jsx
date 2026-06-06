function HoldingsTable({ holdings }) {
  return (
    <div className="table-scroll">
      <table className="holdings-table">
        <thead><tr><th>Holding</th><th>Type</th><th>Identifier</th><th className="number">Market Value</th><th className="number">Weight</th><th className="number">Gain/Loss</th></tr></thead>
        <tbody>
          {holdings.map((holding) => (
            <tr key={`${holding.name}-${holding.asset_type}`}>
              <td><strong>{holding.name}</strong><span>{holding.ticker || holding.currency}</span></td>
              <td>{holding.asset_type}</td>
              <td>{holding.isin || holding.sedol || holding.ticker}</td>
              <td className="number">{money(holding.market_value)}</td>
              <td className="number">{percent(holding.weight)}</td>
              <td className={`number ${holding.gain_loss < 0 ? "negative" : holding.gain_loss > 0 ? "positive" : ""}`}>{money(holding.gain_loss)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function money(value) {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 }).format(value);
}

function percent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

export default HoldingsTable;
