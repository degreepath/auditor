import * as React from "react";
import { useFetch } from "react-async";
import styled from "styled-components";
import { Helmet } from "react-helmet";
import "./App.css";
import { StudentDetail } from "./student";
import { StudentOverviewRecord } from "./types";
import { Loading } from "./loading";

function StudentList({ results }: { results: StudentOverviewRecord[] }) {
  let url = new URL(window.location as any);

  let resultId = url.searchParams.get("result");
  if (resultId) {
    return <StudentDetail resultId={parseInt(resultId, 10)} />;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>ID Number</th>
          <th>Name</th>
          <th>Advisor</th>
          <th>Status</th>
          <th>Progress</th>
          <th>Area Identifier</th>
        </tr>
      </thead>
      <tbody>
        {results.map(result => {
          let handler = () => {
            url.searchParams.set("result", result.result_id.toString());
            window.location.assign(url.toString());
          };

          return (
            <StyledStudentRow key={result.result_id} onClick={handler}>
              <StudentRow record={result} />
            </StyledStudentRow>
          );
        })}
      </tbody>
    </table>
  );
}

let StyledStudentRow = styled.tr`
  --hover-bg: var(--md-grey-400);
  --normal-bg: var(--md-grey-200);
  --accent-bg: var(--md-grey-300);

  @media (prefers-color-scheme: dark) {
    --hover-bg: var(--md-grey-900);
    --normal-bg: var(--md-grey-800);
    --accent-bg: var(--md-grey-700);
  }

  background-color: var(--normal-bg);

  &:nth-child(even) {
    background-color: var(--accent-bg);
  }

  &:hover {
    cursor: pointer;
    background-color: var(--hover-bg);
  }
`;

function StudentRow(props: { record: StudentOverviewRecord }) {
  let { record } = props;
  return (
    <>
      <td style={{ padding: "0 0.25em" }}>{record.student_id}</td>
      <td style={{ padding: "0.5em 1em" }}>
        <button
          type="button"
          style={{
            border: "0",
            appearance: "none",
            fontSize: "1em",
            margin: 0,
            padding: 0,
            textDecoration: "underline",
            textAlign: "left",
            color: "inherit",
            cursor: "inherit",
            backgroundColor: "inherit"
          }}
        >
          {record.student_name}
        </button>
      </td>
      <td style={{ padding: "0.5em 1em" }}>{record.student_advisor}</td>
      <td style={{ padding: "0 1em", textAlign: "center" }}>
        {record.result_ok ? "❇️ Complete" : "️⚠️ Incomplete"}
      </td>
      <td style={{ padding: "0 1em", whiteSpace: "nowrap" }}>
        <progress value={record.result_rank} max={record.success_rank} />
      </td>
      <td style={{ padding: "0.5em 1em", whiteSpace: "pre-wrap" }}>
        {record.area_ident.split(" → ").join("\n→ ")}
      </td>
    </>
  );
}

const App: React.FC = () => {
  let fetchUrl = "https://www.stolaf.edu/sis/degreepath/cf/list.cfm";

  let { data, isLoading, error } = useFetch(fetchUrl, {
    headers: { accept: "application/json" }
  });

  let e = (error as any) as Response | null;

  let [errorDetail, setErrorDetail] = React.useState<any>(null);

  React.useEffect(() => {
    if (!e) {
      setErrorDetail(null);
      return;
    }
    e.json().then(setErrorDetail);
  }, [setErrorDetail, e]);

  return (
    <div className="degreepath">
      <Helmet>
        <title>Degree Audit | St. Olaf College</title>
      </Helmet>

      {isLoading ? <Loading /> : null}

      {e && errorDetail ? (
        <pre>
          <b>
            {e.status} {e.statusText}
          </b>
          {"\n"}
          <span
            dangerouslySetInnerHTML={{ __html: errorDetail.detail.output }}
          />
        </pre>
      ) : null}

      {!e && !isLoading ? <StudentList results={data || []} /> : null}
    </div>
  );
};

export default App;
