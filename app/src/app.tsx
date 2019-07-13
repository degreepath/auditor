import * as React from "react";
import "./app.css";
import { AreaResult } from "./result";
import { EvaluationResultT, AreaOfStudy } from "./types";

const App: React.FC = () => {
  let result: null | EvaluationResultT = (window as any).__dpResult;
  let error: null | object = (window as any).__dpError;
  let area: AreaOfStudy = (window as any).__dpArea;

  if (error) {
    return (
      <pre>
        <b>{JSON.stringify(error, null, 2)}</b>
      </pre>
    );
  }

  if (!result) {
    return <p>That student's audit is not yet complete.</p>;
  }

  return (
    <div className="degreepath">
      <AreaResult area={area} result={result} />
    </div>
  );
};

export default App;
