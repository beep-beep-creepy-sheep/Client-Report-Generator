import { Download } from "lucide-react";

function ReportPreview({ report }) {
  return (
    <article className="report-preview">
      <header><div><p className="eyebrow">Rendered static sample</p><h3>{report.title}</h3><span>{report.basis}</span></div><a className="button" href="/sample_report.md" download><Download size={17} /> Static Markdown</a></header>
      <div className="report-body">
        {report.sections.map((section) => <section key={section.heading}><h4>{section.heading}</h4><p>{section.body}</p></section>)}
        <section><h4>References</h4><ol>{report.references.map((reference) => <li key={reference}>{reference}</li>)}</ol></section>
      </div>
    </article>
  );
}

export default ReportPreview;
