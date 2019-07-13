import * as React from "react";
import { ResultBlock } from "./common";
import { ICourseRule, CourseResultT, Course } from "../types";
import { StatusIcon, RuleSection } from "../components";

export function CourseResult(props: ResultBlock<ICourseRule | CourseResultT>) {
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
      <StatusIcon icon={result.ok ? "ok" : "warn"} />

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
