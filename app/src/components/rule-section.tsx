import styled from "styled-components";

import { StatusIconCore } from "./status-icon";

interface Props {
  readonly success: boolean;
  readonly border?: boolean;
  readonly skipped?: boolean;
}

export const RuleSection = styled.section<Props>`
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

  & > ${StatusIconCore} {
    grid-column: 1;
  }

  & > *:not(${StatusIconCore}) {
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
