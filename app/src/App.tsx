import * as React from "react";
import { Helmet } from "react-helmet";
import "./App.css";
import { StudentDetail } from "./student";

const App: React.FC = () => {
  let url = new URL(window.location as any);

  let resultId = url.searchParams.get("result");

  return (
    <div className="degreepath">
      <Helmet>
        <title>Degree Audit | St. Olaf College</title>
      </Helmet>

      {resultId ? (
        <StudentDetail resultId={parseInt(resultId, 10)} />
      ) : (
        <p>No result found.</p>
      )}
    </div>
  );
};

export default App;
