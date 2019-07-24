import * as React from "react";
import { StatusIcon, RuleSection } from "../components";
import { ResultBlock } from "./common";
import { EvaluatedRequirement } from "../types";
import { RuleResult } from "./index";

export function RequirementResult(props: ResultBlock<EvaluatedRequirement>) {
  let { result, isOpen, onClick, transcript } = props;
  return (
    <RuleSection success={result.ok}>
      <StatusIcon icon={result.ok ? "ok" : "warn"} />

      <header onClick={onClick}>
        <p>
          Requirement <i>“{result.name}”</i> is{" "}
          {result.ok ? <>complete!</> : <>incomplete.</>}
        </p>
      </header>

      {isOpen ? (
        <RuleResult result={result.result} transcript={transcript} />
      ) : null}
    </RuleSection>
  );
}
