const palette = ["#315f72", "#6b7f3f", "#b1862e", "#7a6461", "#4d5a78"];

function AllocationChart({ allocation, compact = false }) {
  return (
    <div className={`allocation-chart ${compact ? "compact" : ""}`}>
      <div className="allocation-strip">{allocation.map((item, index) => <span key={item.asset_type} style={{ width: `${item.weight * 100}%`, backgroundColor: palette[index % palette.length] }} title={`${item.asset_type}: ${percent(item.weight)}`} />)}</div>
      <div className="allocation-list">{allocation.map((item, index) => <div className="allocation-item" key={item.asset_type}><i style={{ backgroundColor: palette[index % palette.length] }} /><span>{item.asset_type}</span><strong>{percent(item.weight)}</strong></div>)}</div>
    </div>
  );
}

function percent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

export default AllocationChart;
