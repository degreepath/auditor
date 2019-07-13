import * as React from "react";
import { ResultBlock } from "./common";
import { IReferenceRule } from "../types";
import { RuleSection } from "../components";

export function ReferenceResult(props: ResultBlock<IReferenceRule>) {
  let { result, onClick } = props;
  return (
    <RuleSection success={result.ok}>
      <header onClick={onClick}>
        <p>reference</p>
      </header>
    </RuleSection>
  );
}
