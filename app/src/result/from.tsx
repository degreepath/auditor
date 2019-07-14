import * as React from "react";
import { ResultBlock } from "./common";
import { IFromRule, FromResultT } from "../types";
import { StatusIcon, RuleSection, WhereClause } from "../components";

export function FromResult(props: ResultBlock<IFromRule | FromResultT>) {
  let { result, isOpen, onClick } = props;

  if (!result.claims) {
    throw new Error("claims should be defined");
  }

  let intro: null | React.ReactNode = null;

  if (
    result.source.mode === "student" &&
    result.source.itemtype === "courses"
  ) {
    intro = <p>Given the courses from the transcript…</p>;
  }

  if (!intro) {
    throw new Error("unexpected lack of from-rule header");
  }

  let limits: null | React.ReactNode = null;
  if (result.limit.length) {
    limits = (
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
    );
  }

  let where: null | React.ReactNode = null;
  if (result.where) {
    where = (
      <details open>
        <summary style={{ display: "flex", alignItems: "center" }}>
          <p>Subject to the following restrictions…</p>
        </summary>

        <WhereClause clause={result.where} />
      </details>
    );
  }

  return (
    <RuleSection success={result.ok}>
      <StatusIcon icon={result.ok ? "ok" : "warn"} />

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
