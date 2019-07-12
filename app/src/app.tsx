import * as React from "react";
import "./App.css";
import { StudentDetail } from "./student";
import { AreaResult } from "./result";
import { StudentResult } from "./types";

const App: React.FC = () => {
  let result = (window as any).__dpResult;
  let error = (window as any).__dpError;
  let area = (window as any).__dpArea;

  if (error && typeof error.message !== "undefined") {
    return (
      <pre>
        <b>{error.message}</b>
      </pre>
    );
  }

  if (!result) {
    return <p>No result record found for result ID {resultId}.</p>;
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
