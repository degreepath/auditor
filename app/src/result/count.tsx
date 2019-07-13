import * as React from "react";
import { StatusIcon, RuleSection } from "../components";
import { ResultBlock } from "./common";
import { CountResultT, ICountRule, IRule, EvaluationResultT } from "../types";
import { RuleResult } from "./index";

export function CountResult(props: ResultBlock<ICountRule | CountResultT>) {
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
      <StatusIcon icon={result.ok ? "ok" : "warn"} />

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

function allItemsAreCourseRules(rule: IRule | EvaluationResultT): boolean {
  if (rule.type !== "count") {
    return false;
  }

  return rule.items.every(
    r => r.type === "course" || allItemsAreCourseRules(r),
  );
}
