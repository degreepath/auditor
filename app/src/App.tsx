import * as React from "react";
import { useFetch } from "react-async";
import styled from "styled-components";
import { Helmet } from "react-helmet";
import "./App.css";

type AreaOfStudy = {
  name: string;
  degree: string;
  requirements: { string: UnevaluatedRequirement };
  result: Rule;
  type: "major" | "concentration" | "emphasis" | "degree";
  attributes: {};
  catalog: string;
  limit: Limit[];
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

type StudentRecord = {
  advisor: string;
  concentrations: string[];
  courses: Course[];
  degrees: string[];
  emphases: string[];
  graduation: number;
  majors: string[];
  matriculation: number;
  name: string;
  stnum: number;
};

type Result =
  | { stnum: number; action: "not-started" }
  | { stnum: number; action: "start" }
  | CompleteResult
  | { stnum: number; action: "in-progress"; count: number };

type CompleteResult = {
  stnum: number;
  action: "complete";
  area: AreaOfStudy;
  avg_iter: string;
  count: number;
  elapsed: string;
  result: EvaluationResult;
  student: StudentRecord;
};

function StudentList({ results }: { results: Result[] }) {
  let students = new Map<number, Result[]>();

  results.forEach(row => {
    let record = students.get(row.stnum);
    if (!record) {
      record = [];
      students.set(row.stnum, record);
    }
    record.push(row);
  });

  let withStatus = [...students.entries()].map(([stnum, logEntries]) => {
    let entry = logEntries.find(e => e.action === "complete") ||
      logEntries.find(e => e.action === "in-progress") ||
      logEntries.find(e => e.action === "start") || {
        stnum,
        action: "not-started"
      };

    return entry;
  });

  withStatus.sort((a, b) =>
    a.stnum < b.stnum ? -1 : a.stnum === b.stnum ? 0 : 1
  );

  let url = new URL(window.location as any);

  let selectedStnum = url.searchParams.get("stnum");
  if (selectedStnum) {
    return (
      <StudentDetail
        record={withStatus.find(s => s.stnum.toString() === selectedStnum)}
      />
    );
  }

  let maxRank = Math.max(
    ...withStatus.map(r => (r.action === "complete" ? r.result.rank : 0))
  );

  return (
    <table>
      <thead>
        <tr>
          <th>ID Number</th>
          <th>Name</th>
          <th>Status</th>
          <th>Progress</th>
          <th>Elapsed</th>
          <th>Stats</th>
        </tr>
      </thead>
      <tbody>
        {withStatus.map(result => {
          let handler = () => {
            url.searchParams.set("stnum", result.stnum.toString());
            window.location.assign(url.toString());
          };

          return (
            <StyledStudentRow key={result.stnum} onClick={handler}>
              {result.action === "complete" ? (
                <StudentRow
                  key={result.stnum}
                  record={result}
                  onClick={handler}
                  maxRank={maxRank}
                />
              ) : (
                <React.Fragment key={result.stnum}>
                  <td>{result.stnum}</td>
                  <td />
                  <td>{result.action}</td>
                  <td />
                  <td />
                  <td />
                </React.Fragment>
              )}
            </StyledStudentRow>
          );
        })}
      </tbody>
    </table>
  );
}

let StyledStudentRow = styled.tr`
  --hover-bg: var(--md-grey-300);
  --accent-bg: var(--md-grey-200);

  @media (prefers-color-scheme: dark) {
    --hover-bg: var(--md-grey-700);
    --accent-bg: var(--md-grey-800);
  }

  &:nth-child(even) {
    background-color: var(--accent-bg);
  }

  &:hover {
    cursor: pointer;
    background-color: var(--hover-bg);
  }
`;

function StudentRow(props: {
  record: CompleteResult;
  onClick: () => any;
  maxRank: number;
}) {
  let { record, onClick, maxRank } = props;
  return (
    <>
      <td style={{ padding: "0 1em" }}>{record.stnum}</td>
      <td style={{ padding: "0.5em 1em" }}>
        <button
          type="button"
          onClick={() => onClick()}
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
          {record.student.name}
        </button>
      </td>
      <td style={{ padding: "0 1em" }}>
        {record.result.ok ? "Complete" : "Incomplete"}
      </td>
      <td style={{ padding: "0 1em", whiteSpace: "nowrap" }}>
        {record.result.ok ? "❇️" : "️⚠️"}
        <progress value={record.result.rank} max={maxRank} />
      </td>
      <td style={{ padding: "0 1em" }}>{record.elapsed}</td>
      <td style={{ padding: "0 1em" }}>
        <div style={{ whiteSpace: "nowrap" }}>
          {record.count} tries at {record.avg_iter}
        </div>
      </td>
    </>
  );
}

function StudentDetail({ record }: { record?: Result }) {
  if (!record) {
    return <p>No student found by that stnum.</p>;
  }

  if (record.action !== "complete") {
    return <p>That student's audit is not yet complete.</p>;
  }

  let { student, result, area } = record;

  console.log(record);

  let progress = result.rank;
  let progressMax = 22;

  let auditedDegrees = new Set([area.type === "degree" ? area.name : null]);
  let auditedMajors = new Set([area.type === "major" ? area.name : null]);
  let auditedConcentrations = new Set([
    area.type === "concentration" ? area.name : null
  ]);

  let url = new URL(window.location as any);
  let navigate = (key: "major" | "degree" | "concentration", value: string) => {
    url.searchParams.set(key, value);
    window.location.assign(url.toString());
  };

  let selectedDegree = url.searchParams.get("degree");
  let selectedMajor = url.searchParams.get("major");
  let selectedConcentration = url.searchParams.get("concentration");

  return (
    <div>
      <Helmet>
        <title>{student.name} | Degree Audit | St. Olaf College</title>
      </Helmet>

      <button
        onClick={() => {
          url.searchParams.delete("major");
          url.searchParams.delete("concentration");
          url.searchParams.delete("degree");
          url.searchParams.delete("stnum");
          window.location.assign(url.toString());
        }}
        type="button"
      >
        Back to Student List
      </button>

      <select>
        <option>foo</option>
      </select>

      <h1>
        The degree audit for{" "}
        <i>
          <b>{student.name}</b>
        </i>
      </h1>

      <header>
        <dl style={{ display: "grid", gridTemplateColumns: "max-content 1fr" }}>
          <dt>Anticipated Graduation Date</dt>
          <dd>MM/YYYY</dd>

          <dt>Student Number</dt>
          <dd>{student.stnum}</dd>

          <dt>Overall GPA</dt>
          <dd>0.00</dd>

          <dt>Advisor</dt>
          <dd>{student.advisor}</dd>

          <dt>Classification</dt>
          <dd>(tbd: senior/junior/sophomore/first-year)</dd>

          <dt>Catalog Year</dt>
          <dd>{student.matriculation}</dd>

          <dt>Progress</dt>
          <dd>
            <progress value={progress} max={progressMax} />
          </dd>
        </dl>
      </header>

      <nav>
        <AreaPicker>
          <dt />
          <dd>
            <AreaChoiceButton
              type="button"
              disabled={false}
              active={
                !selectedDegree && !selectedMajor && !selectedConcentration
              }
              onClick={() => {
                url.searchParams.delete("degree");
                url.searchParams.delete("major");
                url.searchParams.delete("concentration");
                window.location.assign(url.toString());
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
                disabled={!auditedDegrees.has(d)}
                active={selectedDegree === d}
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
                disabled={!auditedMajors.has(d)}
                active={selectedMajor === d}
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
                    disabled={!auditedConcentrations.has(d)}
                    active={selectedConcentration === d}
                    onClick={() => navigate("concentration", d)}
                  >
                    {d}
                  </AreaChoiceButton>
                ))}
              </dd>
            </>
          ) : null}
        </AreaPicker>
      </nav>

      {selectedDegree || selectedMajor || selectedConcentration ? (
        <AreaResult area={area} result={result} />
      ) : (
        <>
          <p>No area selected. Please select an area above.</p>

          <TranscriptList courses={student.courses} />
        </>
      )}
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

      <RuleResult result={result} />
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
  grid-template-areas:
    "status header"
    "status details";
  grid-template-columns: max-content 1fr;
  align-items: baseline;
  column-gap: 0.85em;

  & > ${StatusIcon} {
    grid-area: status;
  }

  & > *:not(${StatusIcon}) {
    grid-area: "details";
  }

  & > header {
    grid-area: header;
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

function RuleResult({ result }: { result: EvaluationResult | Rule }) {
  // console.log(result);

  let [isOpen, setOpenState] = React.useState(!result.ok);
  let handler = () => setOpenState(!isOpen);

  if (result.type === "count") {
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

      <header onClick={onClick}>
        {intro}
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
      </header>

      {isOpen ? (
        <ul>
          {result.claims.map(c => (
            <li>{c.claim.course_id}</li>
          ))}
        </ul>
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
    let key = <>clause.key</>;
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
  let url = new URL(window.location as any);

  let fetchUrl = "https://www.stolaf.edu/sis/degreepath/public-ndjson.cfm";
  if (url.searchParams.has("stnum")) {
    let stnum = url.searchParams.get("stnum");
    fetchUrl = `https://www.stolaf.edu/sis/degreepath/cf/test.cfm?stnum=${stnum}`;
  }

  let { data, isLoading } = useFetch(fetchUrl);

  let [lines, setLines] = React.useState<Result[]>([]);

  React.useEffect(() => {
    if (!data) {
      return;
    }
    data.text().then((allLines: string) => {
      let dataLines: Result[] = allLines
        .split("\n")
        .filter(l => l.trim())
        .map((l: string) => JSON.parse(l));

      setLines(dataLines);
    });
  }, [data]);

  return (
    <div className="degreepath profile--coatedgracol2006">
      <Helmet>
        <title>Degree Audit | St. Olaf College</title>
      </Helmet>

      {isLoading ? (
        <div className="App">
          <header className="App-header">
            <p>Loading…</p>
          </header>
        </div>
      ) : null}

      <StudentList results={lines} />
    </div>
  );
};

export default App;
