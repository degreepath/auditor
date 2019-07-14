import * as React from "react";
import { ResultBlock } from "./common";
import { ICourseRule, CourseResultT, Course } from "../types";
import { StatusIcon, RuleSection } from "../components";

export function CourseResult(props: ResultBlock<ICourseRule | CourseResultT>) {
  let { result, isOpen, onClick } = props;

  if (result.hidden && result.status !== "pass") {
    return null;
  }

  //
  // TODO:             claim = rule["claims"][0]["claim"]
  //                   course = next(c for c in transcript if c.clbid == claim["clbid"])
  //
  // ie, we need to get the transcript from the server, and pass it down into here
  //

  let claimed = result.claims
    ? result.claims[0]
      ? result.claims[0].claim.clbid
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
