import * as React from "react";
import styled from "styled-components";

let icons = {
  ok: "️️❇️",
  warn: "️️️⚠️",
};

let labels: typeof icons = {
  ok: "OK",
  warn: "Warning",
};

export const StatusIconCore = styled.span``;

export const StatusIcon = ({ icon }: { icon: keyof typeof icons }) => (
  <StatusIconCore role="img" aria-label={labels[icon]}>
    {icons[icon]}
  </StatusIconCore>
);
