import "./app.css";

import * as React from "react";
import { RuleResult } from "./result";
import { EvaluationResultT } from "./types";

export function App() {
  let result: null | EvaluationResultT = (window as any).__dpResult;
  let error: null | object = (window as any).__dpError;

  if (error) {
    return <pre>{JSON.stringify(error, null, 2)}</pre>;
  }

  if (!result) {
    return <p>That student's audit is not yet complete.</p>;
  }

  return (
    <article className="degreepath">
      <header>
        <dl>
          <dt>Status</dt>
          <dd>{result.ok ? "❇️ Complete" : "⚠️ Incomplete"}</dd>

          <dt>In-Major GPA</dt>
          <dd>0.00</dd>
        </dl>
      </header>

      <RuleResult result={result} topLevel={true} />
    </article>
  );
}
