import * as React from "react";
import { RuleSection, StatusIcon } from "../components";
import { EvaluationResultT, IRule } from "../types";

import { CountResult } from "./count";
import { CourseResult } from "./course";
import { FromResult } from "./from";
import { ReferenceResult } from "./reference";
import { RequirementResult } from "./requirement";

export function RuleResult(args: {
  result: EvaluationResultT | IRule;
  topLevel?: boolean;
}) {
  let { result, topLevel = false } = args;

  let [isOpen, setOpenState] = React.useState(!result.ok);
  let handler = () => setOpenState(!isOpen);

  if (result.type === "count") {
    if (topLevel) {
      isOpen = true;
    }
    return <CountResult result={result} isOpen={isOpen} onClick={handler} />;
  } else if (result.type === "course") {
    return <CourseResult result={result} isOpen={isOpen} onClick={handler} />;
  } else if (result.type === "from") {
    return <FromResult result={result} isOpen={isOpen} onClick={handler} />;
  } else if (result.type === "reference") {
    return (
      <ReferenceResult result={result} isOpen={isOpen} onClick={handler} />
    );
  } else if (result.type === "requirement") {
    return (
      <RequirementResult result={result} isOpen={isOpen} onClick={handler} />
    );
  } else {
    console.error(result);
    return (
      <RuleSection success={false}>
        <StatusIcon icon="warn" />
        Unknown rule type: {(result as any).type}
      </RuleSection>
    );
  }
}
