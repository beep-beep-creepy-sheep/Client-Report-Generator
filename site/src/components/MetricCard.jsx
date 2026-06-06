function MetricCard({ label, value, detail = "", tone = "neutral" }) {
  return <article className={`metric-card tone-${tone}`}><span>{label}</span><strong>{value}</strong>{detail ? <p>{detail}</p> : null}</article>;
}

export default MetricCard;
