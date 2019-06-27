import * as React from "react";
import { useFetch } from "react-async";
import styled from "styled-components";
import { Helmet } from "react-helmet";
import "./App.css";

type AreaOfStudy = {
  id: number;
  name: string;
  type: string;
  degree: null | string;
  catalog_year: number;
  success_rank: number;
};

interface BaseRule {
  type: string;
  state: "rule" | "solution" | "result";
  status: "skip" | "pass" | "fail";
  ok: boolean;
  rank: number;
}

interface CourseRule extends BaseRule {
  type: "course";
  claims?: ClaimList[];
  allow_claimed: boolean;
  course: string;
  grade?: string;
  hidden: boolean;
}

interface CountRule extends BaseRule {
  type: "count";
  claims: ClaimList[];
  count: number;
  items: (Rule | EvaluationResult)[];
}

interface ReferenceRule extends BaseRule {
  type: "reference";
  name: string;
}

interface FromRule extends BaseRule {
  type: "from";
  source: {
    itemtype: "courses";
    mode: "student";
    requirements: string[];
    saves: string[];
  };
  claims?: ClaimList[];
  limit: Limit[];
  where: WhereClause;
  action: {
    command: "count";
    compare_to: any;
    operator: Operator;
    source: string;
  };
}

type Limit = { at_most: number; where: WhereClause };
type Rule = CourseRule | CountRule | ReferenceRule | FromRule;
type CourseResult = CourseRule & { state: "result" };
type CountResult = CountRule & { state: "result" };
type ReferenceResult = ReferenceRule & { state: "result" };
type FromResult = FromRule & { state: "result" };
type EvaluationResult =
  | CourseResult
  | CountResult
  | ReferenceResult
  | EvaluatedRequirement
  | FromResult;

type Claim = {
  claimant_path: string[];
  course: Course;
  course_id: string;
  value: CourseRule;
};

type ClaimList = {
  claim: Claim;
  claimant_path: string[];
};

type Operator = "EqualTo" | "GreaterThanOrEqualTo";

type WhereClause =
  | { type: "single-clause"; operator: Operator; key: string; expected: any }
  | { type: "and-clause"; children: WhereClause[] }
  | { type: "or-clause"; children: WhereClause[] };

type UnevaluatedRequirement = {
  audited_by?: string;
  contract: boolean;
  message: string;
  name: string;
  requirements: { string: UnevaluatedRequirement };
  result: Rule;
  saves: {};
};

type EvaluatedRequirement = {
  audited_by?: string;
  contract: boolean;
  message: string;
  name: string;
  result: EvaluationResult;
  saves: {};
  ok: boolean;
  claims: ClaimList[];
  rank: number;
  type: "requirement";
};

type Course = {
  clbid: string;
  course: string;
  credits: number;
  gereqs: [];
  grade: string;
  graded: string;
  incomplete: false;
  is_repeat: false;
  lab: false;
  name: string;
  number: string;
  section: string;
  semester?: number;
  subjects: string[];
  term: number | { year: number; semester: number };
  transcript_code: string;
  year?: number;
};

type StudentOverviewRecord = {
  result_id: number;
  student_id: string;
  student_name: string;
  student_advisor: string;
  anticipated_graduation: string;
  classification: string;
  area_id: number;
  result_ts: string;
  result_rank: number;
  success_rank: number;
  result_ok: boolean;
  area_ident: string;
};

type StudentResult = {
  info: {
    result_id: number;
    student_id: string;
    student_name: string;
    student_advisor: string;
    anticipated_graduation: string;
    classification: string;
    area_id: number;
    result_ts: string;
    result_rank: number;
    success_rank: number;
    result_ok: boolean;
    area_ident: string;
  };
  student: {
    anticipated_graduation: string;
    catalog_year: number;
    degrees: string[];
    majors: string[];
    id: string;
    concentrations: string[];
    input_courses: Course[];
    matriculation_year: number;
    student_advisor: string;
    student_name: string;
  };
  area: AreaOfStudy;
  result: null | EvaluationResult;
};

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

function StudentDetail({ resultId }: { resultId?: number }) {
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

function AreaResult(props: { area: AreaOfStudy; result: EvaluationResult }) {
  let { area, result } = props;

  return (
    <article>
      <header>
        <h2>
          The <i>{area.name}</i> {area.type}
        </h2>

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

interface RuleSectionProps {
  readonly success: boolean;
  readonly border?: boolean;
  readonly skipped?: boolean;
}

const StatusIcon = styled.span``;

const RuleSection = styled.section<RuleSectionProps>`
  border-style: solid;
  border-color: ${props =>
    props.success ? "var(--success-border)" : "var(--incomplete-border)"};
  border-width: ${({ border = true }) => (border ? "1px" : "0")};
  border-radius: 4px;
  padding: 0.5em 1em 0.5em 1em;
  background-color: ${props =>
    props.success ? "var(--success-bg)" : "var(--incomplete-bg)"};
  color: ${props =>
    props.success ? "var(--success-fg)" : "var(--incomplete-fg)"};

  display: grid;
  grid-template-columns: max-content 1fr;
  align-items: baseline;
  column-gap: 0.85em;

  & > ${StatusIcon} {
    grid-column: 1;
  }

  & > *:not(${StatusIcon}) {
    grid-column: 2;
  }

  & > header {
    grid-column: 2;
  }

  opacity: ${props => (props.skipped ? "0.5" : "1")};

  & + & {
    margin-top: 0.5em;
  }

  p {
    margin: 0.5em 0;
  }

  & > header {
    cursor: ns-resize;
  }
`;

function allItemsAreCourseRules(rule: Rule | EvaluationResult): boolean {
  if (rule.type !== "count") {
    return false;
  }

  return rule.items.every(
    r => r.type === "course" || allItemsAreCourseRules(r)
  );
}

function RuleResult({
  result,
  topLevel = false
}: {
  result: EvaluationResult | Rule;
  topLevel?: boolean;
}) {
  // console.log(result);

  let [isOpen, setOpenState] = React.useState(!result.ok);
  let handler = () => setOpenState(!isOpen);

  if (result.type === "count") {
    if (topLevel) {
      isOpen = true;
    }
    return <CountResult result={result} isOpen={isOpen} onClick={handler} />;
  }

  if (result.type === "course") {
    return <CourseResult result={result} isOpen={isOpen} onClick={handler} />;
  }

  if (result.type === "from") {
    return <FromResult result={result} isOpen={isOpen} onClick={handler} />;
  }

  if (result.type === "reference") {
    return (
      <ReferenceResult result={result} isOpen={isOpen} onClick={handler} />
    );
  }

  if (result.type === "requirement") {
    return (
      <RequirementResult result={result} isOpen={isOpen} onClick={handler} />
    );
  }

  console.log(result);
  throw new Error(`Unknown rule type: ${(result as any).type}`);
}

interface ResultBlock<T> {
  result: T;
  isOpen: boolean;
  onClick: () => any;
}

function CourseResult(props: ResultBlock<CourseRule | CourseResult>) {
  let { result, isOpen, onClick } = props;

  if (result.hidden && result.status !== "pass") {
    return null;
  }

  let claimed = result.claims
    ? result.claims[0]
      ? result.claims[0].claim.course
      : null
    : null;

  return (
    <RuleSection success={result.ok} skipped={result.status === "skip"}>
      <StatusIcon>{result.ok ? `️️❇️` : `️️️⚠️`}</StatusIcon>

      <header onClick={onClick}>
        <p>
          {result.ok ? (
            <>
              {result.course}: {(claimed as Course).name}
            </>
          ) : result.status === "skip" ? (
            <>{result.course}</>
          ) : (
            <>{result.course}</>
          )}
        </p>
      </header>

      {isOpen && claimed && typeof claimed.term !== "number" ? (
        <>
          <p>
            Taken in {claimed.term.year}-{claimed.term.semester}
          </p>
        </>
      ) : null}
    </RuleSection>
  );
}

function FromResult(props: ResultBlock<FromRule | FromResult>) {
  let { result, isOpen, onClick } = props;

  if (!result.claims) {
    throw new Error("claims should be defined");
  }

  let intro: null | React.ReactNode = null;

  if (
    result.source.mode === "student" &&
    result.source.itemtype === "courses"
  ) {
    intro = (
      <>
        <p>Given the courses from the transcript…</p>
      </>
    );
  }

  if (!intro) {
    throw new Error("unexpected lack of from-rule header");
  }

  let limits: null | React.ReactNode = null;
  if (result.limit.length) {
    limits = (
      <>
        <details open>
          <summary style={{ display: "flex", alignItems: "center" }}>
            <p>Subject to the following restrictions…</p>
          </summary>

          {result.limit.map(l => {
            return (
              <>
                At most {l.at_most} courses that match{" "}
                <WhereClause clause={l.where} />
              </>
            );
          })}
        </details>
      </>
    );
  }

  let where: null | React.ReactNode = null;
  if (result.where) {
    where = (
      <>
        <details open>
          <summary style={{ display: "flex", alignItems: "center" }}>
            <p>Subject to the following restrictions…</p>
          </summary>

          <WhereClause clause={result.where} />
        </details>
      </>
    );
  }

  return (
    <RuleSection success={result.ok}>
      <StatusIcon>{result.ok ? `️️❇️` : `️️️⚠️`}</StatusIcon>

      <header onClick={onClick}>{intro}</header>

      {isOpen ? (
        <>
          {limits}
          {where}

          <p>
            There must be {"at least"} {result.action.compare_to}{" "}
            {result.action.compare_to === 1 ? "course" : "courses"}.
          </p>

          <p>
            {result.ok ? (
              result.claims.length === 1 ? (
                <>There was a course!</>
              ) : (
                <>There were {result.claims.length} courses!</>
              )
            ) : result.claims.length === 1 ? (
              <>There was only 1 course.</>
            ) : (
              <>️There were only {result.claims.length} courses.</>
            )}
          </p>

          <ul>
            {result.claims.map(c => (
              <li>{c.claim.course_id}</li>
            ))}
          </ul>
        </>
      ) : null}
    </RuleSection>
  );
}

function CountResult(props: ResultBlock<CountRule | CountResult>) {
  let { result, isOpen, onClick } = props;

  let successfulItemCount = result.items.filter(item => item.ok).length;
  let totalItemCount = result.items.filter(
    item => item.type !== "course" || !item.hidden
  ).length;
  let requiredItemCount = result.count;

  let containsOnlyCourses = allItemsAreCourseRules(result);

  if (
    containsOnlyCourses &&
    requiredItemCount === 1 &&
    successfulItemCount === 1
  ) {
    return (
      <RuleResult result={result.items.find(r => r.ok) as EvaluationResult} />
    );
  }

  return (
    <RuleSection success={result.ok}>
      <StatusIcon>{result.ok ? `️️❇️` : `️️️⚠️`}</StatusIcon>

      <header onClick={onClick}>
        <p>
          {result.ok ? (
            <>
              {requiredItemCount === 1 && totalItemCount === 2 ? (
                <>Either item is required blah</>
              ) : requiredItemCount === 2 && totalItemCount === 2 ? (
                <>Both items were successful</>
              ) : requiredItemCount === totalItemCount ? (
                <>All items were successful</>
              ) : requiredItemCount === 1 ? (
                <>1 item is required blah</>
              ) : (
                <>
                  {requiredItemCount} of {totalItemCount}{" "}
                  {totalItemCount === 1 ? "item" : "items"}{" "}
                  {totalItemCount === 1 ? "is" : "are"} required
                </>
              )}
            </>
          ) : (
            <>
              {requiredItemCount === 1 && totalItemCount === 2 ? (
                <>Either item is required</>
              ) : requiredItemCount === 2 && totalItemCount === 2 ? (
                <>Both items are required</>
              ) : requiredItemCount === totalItemCount ? (
                <>All items are required</>
              ) : requiredItemCount === 1 ? (
                <>1 item is required</>
              ) : (
                <>
                  {requiredItemCount} of {totalItemCount}{" "}
                  {totalItemCount === 1 ? "item" : "items"}{" "}
                  {totalItemCount === 1 ? "is" : "are"} required
                </>
              )}
            </>
          )}
        </p>
      </header>

      <div>
        {isOpen
          ? result.items.map((item, i) => <RuleResult key={i} result={item} />)
          : null}
      </div>
    </RuleSection>
  );
}

function ReferenceResult(props: ResultBlock<ReferenceRule>) {
  let { result, onClick } = props;
  return (
    <RuleSection success={result.ok}>
      <header onClick={onClick}>
        <p>reference</p>
      </header>
    </RuleSection>
  );
}

function RequirementResult(props: ResultBlock<EvaluatedRequirement>) {
  let { result, isOpen, onClick } = props;
  return (
    <RuleSection success={result.ok}>
      <StatusIcon>{result.ok ? `️️❇️` : `️️️⚠️`}</StatusIcon>
      <header onClick={onClick}>
        <p>
          Requirement <i>“{result.name}”</i> was{" "}
          {result.ok ? <>complete!</> : <>️incomplete.</>}
        </p>
      </header>

      {isOpen ? <RuleResult result={result.result} /> : null}
    </RuleSection>
  );
}

function WhereClause({ clause }: { clause: WhereClause }) {
  if (clause.type === "and-clause") {
    return (
      <dl>
        <dt>
          <strong>ALL:</strong>
        </dt>
        <dd>
          {clause.children.map(clause => (
            <WhereClause clause={clause} />
          ))}
        </dd>
      </dl>
    );
  } else if (clause.type === "or-clause") {
    return (
      <dl>
        <dt>
          <strong>ANY:</strong>
        </dt>
        <dd>
          {clause.children.map(clause => (
            <WhereClause clause={clause} />
          ))}
        </dd>
      </dl>
    );
  } else if (clause.type === "single-clause") {
    let key = <>{clause.key}</>;
    if (clause.key === "gereqs") {
      key = (
        <>
          <abbr
            title="General Education"
            style={{ cursor: "help", textDecoration: "none" }}
          >
            GE
          </abbr>{" "}
          Requirement
        </>
      );
    }

    let operator = <>{clause.operator}</>;
    if (clause.operator === "EqualTo") {
      operator = <>is</>;
    }

    let value = <>{clause.expected}</>;
    if (Array.isArray(clause.expected)) {
      value = <>{clause.expected.join(", ")}</>;
    }

    return (
      <p style={{ marginLeft: "1em" }}>
        <span
          style={{
            backgroundColor: "rgba(0,0,0,0.15)",
            borderRadius: "4px",
            padding: "0 0.25em"
          }}
        >
          {key} {operator} {value}
        </span>
      </p>
    );
  }

  throw new Error("unexpected clause type");
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

const Loading = () => {
  return (
    <div className="App">
      <header className="App-header">
        <p>Loading…</p>
      </header>
    </div>
  );
};

export default App;
