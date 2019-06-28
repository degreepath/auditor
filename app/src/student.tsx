import * as React from "react";
import { useFetch } from "react-async";
import styled from "styled-components";
import { Helmet } from "react-helmet";
import { AreaResult } from "./result";
import { StudentResult, Course } from "./types";
import { Loading } from "./loading";

export function StudentDetail({ resultId }: { resultId?: number }) {
  let fetchUrl = `https://www.stolaf.edu/sis/degreepath/cf/collect.cfm?result=${resultId}`;

  let { data, isLoading, error } = useFetch<StudentResult>(fetchUrl, {
    headers: { accept: "application/json" }
  });

  let e = (error as any) as Response | null;

  let [errorDetail, setErrorDetail] = React.useState<any>(null);

  React.useEffect(() => {
    if (!e) {
      setErrorDetail(null);
      return;
    }
    console.warn(e);
    if (e instanceof Error) {
      setErrorDetail(null);
      return;
    }
    e.json().then(setErrorDetail);
  }, [setErrorDetail, e]);

  if (isLoading) {
    return <Loading />;
  }

  if (error instanceof Error) {
    return (
      <pre>
        <b>{error.message}</b>
      </pre>
    );
  }

  if (e && errorDetail) {
    return (
      <pre>
        <b>
          {e.status} {e.statusText}
        </b>
        {"\n"}
        <span dangerouslySetInnerHTML={{ __html: errorDetail.detail.output }} />
      </pre>
    );
  }

  if (!data) {
    return <p>No result record found for result ID {resultId}.</p>;
  }

  let { student, result, area } = data;

  if (!result) {
    return <p>That student's audit is not yet complete.</p>;
  }

  let progress = result.rank;
  let progressMax = area.success_rank;

  let url = new URL(window.location as any);
  // let navigate = (key: "major" | "degree" | "concentration", value: string) => {
  //   url.searchParams.set(key, value);
  //   window.history.pushState({}, "", url.toString());
  // };

  return (
    <div>
      <Helmet>
        <title>{student.student_name} | Degree Audit | St. Olaf College</title>
      </Helmet>

      <button
        onClick={() => {
          url.searchParams.delete("result");
          window.location.assign(url.toString());
        }}
        type="button"
      >
        Back to Student List
      </button>

      <h1>
        The degree audit for{" "}
        <i>
          <b>{student.student_name}</b>
        </i>
      </h1>

      <header>
        <dl style={{ display: "grid", gridTemplateColumns: "max-content 1fr" }}>
          <dt>Anticipated Graduation Date</dt>
          <dd>{student.anticipated_graduation}</dd>

          <dt>Student Number</dt>
          <dd>{student.id}</dd>

          <dt>Overall GPA</dt>
          <dd>TBC{/*result.overall_gpa*/}</dd>

          <dt>Advisor</dt>
          <dd>{student.student_advisor}</dd>

          <dt>Classification</dt>
          <dd>{(student as any).classification || ""}</dd>

          <dt>Catalog Year</dt>
          <dd>{student.catalog_year}</dd>

          <dt>Progress</dt>
          <dd>
            <progress value={progress} max={progressMax} />
          </dd>
        </dl>
      </header>

      {/*<nav>
          <AreaPicker>
            <dt />
            <dd>
              <AreaChoiceButton
                type="button"
                disabled={false}
                active={!selectedArea}
                onClick={() => {
                  url.searchParams.delete("area");
                  window.history.pushState({}, "", url.toString());
                }}
              >
                Overview
              </AreaChoiceButton>
            </dd>
  
            <dt>{student.degrees.length === 1 ? "Degree" : "Degrees"}</dt>
            <dd>
              {student.degrees.map(d => (
                <AreaChoiceButton
                  key={d}
                  type="button"
                  active={selectedArea ? selectedDegree.name === d : false}
                  onClick={() => navigate("degree", d)}
                >
                  {d}
                </AreaChoiceButton>
              ))}
            </dd>
  
            <dt>{student.majors.length === 1 ? "Major" : "Majors"}</dt>
            <dd>
              {student.majors.map(d => (
                <AreaChoiceButton
                  key={d}
                  type="button"
                  active={selectedMajor ? selectedMajor.name === d : false}
                  onClick={() => navigate("major", d)}
                >
                  {d}
                </AreaChoiceButton>
              ))}
            </dd>
  
            {student.concentrations.length ? (
              <>
                <dt>
                  {student.concentrations.length === 1
                    ? "Concentration"
                    : "Concentrations"}
                </dt>
                <dd>
                  {student.concentrations.map(d => (
                    <AreaChoiceButton
                      key={d}
                      type="button"
                      active={
                        selectedConcentration
                          ? selectedConcentration.name === d
                          : false
                      }
                      onClick={() => navigate("concentration", d)}
                    >
                      {d}
                    </AreaChoiceButton>
                  ))}
                </dd>
              </>
            ) : null}
          </AreaPicker>
                    </nav>*/}

      <AreaResult area={area} result={result} />

      {/* {selectedArea ? (
          <AreaResult area={area} result={result} />
        ) : (
          <>
            <p>No area selected. Please select an area above.</p>
  
            <TranscriptList courses={student.input_courses} />
          </>
        )} */}
    </div>
  );
}

function TranscriptList({ courses }: { courses: Course[] }) {
  courses = [...courses].sort((a, b) =>
    a.course < b.course ? -1 : a.course === b.course ? 0 : 1
  );

  return (
    <table>
      <thead>
        <tr>
          <th>Course</th>
          <th>Name</th>
          <th>Credits</th>
          <th>Grade</th>
          <th>Term</th>
          <th>GE Reqs</th>
        </tr>
      </thead>
      <tbody>
        {courses.map(c => (
          <TranscriptItem key={c.clbid} course={c} />
        ))}
      </tbody>
    </table>
  );
}

function TranscriptItem({ course }: { course: Course }) {
  return (
    <tr>
      <td>{course.course}</td>
      <td style={{ paddingLeft: "1em", paddingRight: "1em" }}>{course.name}</td>
      <td style={{ fontVariantNumeric: "tabular-nums", textAlign: "center" }}>
        {course.credits.toFixed(2)}
      </td>
      <td>{course.grade}</td>
      <td>
        {course.semester === 1
          ? "Fall"
          : course.semester === 2
          ? "Interim"
          : course.semester === 3
          ? "Spring"
          : course.semester === 4
          ? "Summer Session 1"
          : course.semester === 5
          ? "Summer Session 2"
          : course.semester === 9
          ? "Not St. Olaf"
          : "Error"}{" "}
        {course.year}
      </td>
      <td>{course.gereqs.join(" + ")}</td>
    </tr>
  );
}

let AreaPicker = styled.dl`
  display: grid;

  & > dt {
    grid-row: 1;

    font-weight: bold;
    margin-bottom: 0.15em;
  }

  & > dd {
    grid-row: 2;

    margin: 0;
    margin-left: 1em;
  }
`;

let AreaChoiceButton = styled.button<{ active: boolean; disabled?: boolean }>`
  appearance: none;
  background-color: inherit;
  color: inherit;
  border: 0;
  font-size: inherit;
  padding: 0;
  cursor: pointer;

  --bg: ${({ active, disabled }) =>
    active
      ? "var(--black)"
      : disabled
      ? "var(--whitesmoke)"
      : "var(--surface)"};
  --border: ${({ active }) => (active ? "var(--black)" : "var(--surface)")};

  --fg: ${({ active }) => (active ? "var(--white)" : "var(--on-surface)")};

  @media (prefers-color-scheme: dark) {
    --bg: ${({ active, disabled }) =>
      active
        ? "var(--md-grey-600)"
        : disabled
        ? "var(--surface)"
        : "var(--md-grey-800)"};
    --border: ${({ active, disabled }) =>
      active
        ? "var(--md-grey-600)"
        : disabled
        ? "var(--md-grey-800)"
        : "var(--md-grey-800)"};

    --fg: ${({ active }) => (active ? "var(--md-white)" : "var(--on-surface)")};
  }

  border: solid 2px var(--border);
  background-color: var(--bg);
  color: var(--fg);
  font-weight: ${({ active }) => (active ? "bold" : "normal")};

  text-decoration: ${({ active }) => (active ? "underline" : "none")};

  padding: 0.5em 1em;

  &[disabled] {
    color: grey;
    cursor: not-allowed;
    text-decoration: line-through;
  }
`;
