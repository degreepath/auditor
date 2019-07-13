import * as React from "react";
import styled from "styled-components";
import {
  EvaluationResultT,
  IRule,
  ICourseRule,
  CourseResultT,
  FromResultT,
  IFromRule,
  CountResultT,
  ICountRule,
  Course,
  IReferenceRule,
  EvaluatedRequirement,
  WhereClauseT,
} from "./types";

export function RuleResult(args: {
  result: EvaluationResultT | IRule;
  topLevel?: boolean;
}) {
  let { result, topLevel = false } = args;
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

function allItemsAreCourseRules(rule: IRule | EvaluationResultT): boolean {
  if (rule.type !== "count") {
    return false;
  }

  return rule.items.every(
    r => r.type === "course" || allItemsAreCourseRules(r),
  );
}

interface ResultBlock<T> {
  result: T;
  isOpen: boolean;
  onClick: () => any;
}

function CourseResult(props: ResultBlock<ICourseRule | CourseResultT>) {
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

function FromResult(props: ResultBlock<IFromRule | FromResultT>) {
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

function CountResult(props: ResultBlock<ICountRule | CountResultT>) {
  let { result, isOpen, onClick } = props;

  let successfulItemCount = result.items.filter(item => item.ok).length;
  let totalItemCount = result.items.filter(
    item => item.type !== "course" || !item.hidden,
  ).length;
  let requiredItemCount = result.count;

  let containsOnlyCourses = allItemsAreCourseRules(result);

  if (
    containsOnlyCourses &&
    requiredItemCount === 1 &&
    successfulItemCount === 1
  ) {
    return (
      <RuleResult result={result.items.find(r => r.ok) as EvaluationResultT} />
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

function ReferenceResult(props: ResultBlock<IReferenceRule>) {
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

function WhereClause({ clause }: { clause: WhereClauseT }) {
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
            padding: "0 0.25em",
          }}
        >
          {key} {operator} {value}
        </span>
      </p>
    );
  }

  throw new Error("unexpected clause type");
}
