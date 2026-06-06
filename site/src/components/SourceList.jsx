function SourceList({ sources }) {
  return <section className="panel source-panel"><div className="panel-title"><h3>Public Research Sources</h3><span>Static examples</span></div><div className="source-list">{sources.map((source) => <article className="source-card" key={source.title}><div><span>{source.category}</span><strong>{source.title}</strong><p>{source.idea}</p></div><small>{source.source}</small></article>)}</div></section>;
}

export default SourceList;
