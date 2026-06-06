function WorkflowStep({ index, step }) {
  return <article className="workflow-step"><div className="step-index">{String(index).padStart(2, "0")}</div><div><h3>{step.title}</h3><p>{step.description}</p></div></article>;
}

export default WorkflowStep;
