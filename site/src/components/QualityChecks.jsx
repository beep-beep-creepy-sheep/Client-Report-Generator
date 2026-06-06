import { AlertTriangle, CheckCircle2, CircleDashed } from "lucide-react";

function QualityChecks({ checks, flags }) {
  return (
    <div className="panel quality-panel">
      <div className="panel-title"><h3>Quality and Risk Controls</h3><span>{checks.length} checks</span></div>
      <div className="check-list">
        {checks.map((check) => {
          const Icon = check.status === "Pass" ? CheckCircle2 : check.status === "Review" ? CircleDashed : AlertTriangle;
          return <article className={`check-item status-${check.status.toLowerCase()}`} key={check.name}><Icon size={18} /><div><strong>{check.name}</strong><p>{check.detail}</p></div></article>;
        })}
      </div>
      <div className="risk-flags"><strong>Snapshot risk flags</strong><ul>{flags.map((flag) => <li key={flag}>{flag}</li>)}</ul></div>
    </div>
  );
}

export default QualityChecks;
