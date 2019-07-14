import * as React from "react";
import { WhereClauseT } from "../types";

export function WhereClause({ clause }: { clause: WhereClauseT }) {
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
