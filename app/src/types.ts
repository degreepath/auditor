export type AreaOfStudy = {
  id: number;
  code: number;
  name: string;
  type: string;
  degree: null | string;
  catalog_year: number;
  success_rank: number;
};

interface BaseRule {
  type: string;
  state: "rule" | "solution" | "result";
  status: "skip" | "pass" | "fail";
  ok: boolean;
  rank: number;
}

export interface ICourseRule extends BaseRule {
  type: "course";
  claims?: ClaimList[];
  allow_claimed: boolean;
  course: string;
  grade?: string;
  hidden: boolean;
}

export interface ICountRule extends BaseRule {
  type: "count";
  claims: ClaimList[];
  count: number;
  items: (IRule | EvaluationResultT)[];
}

export interface IReferenceRule extends BaseRule {
  type: "reference";
  name: string;
}

export interface IFromRule extends BaseRule {
  type: "from";
  source: {
    itemtype: "courses";
    mode: "student";
    requirements: string[];
    saves: string[];
  };
  claims?: ClaimList[];
  limit: Limit[];
  where: WhereClauseT;
  action: {
    command: "count";
    compare_to: any;
    operator: Operator;
    source: string;
  };
}

type Limit = { at_most: number; where: WhereClauseT };
export type IRule = ICourseRule | ICountRule | IReferenceRule | IFromRule;
export type CourseResultT = ICourseRule & { state: "result" };
export type CountResultT = ICountRule & { state: "result" };
export type ReferenceResultT = IReferenceRule & { state: "result" };
export type FromResultT = IFromRule & { state: "result" };
export type EvaluationResultT =
  | CourseResultT
  | CountResultT
  | ReferenceResultT
  | EvaluatedRequirement
  | FromResultT;

type Claim = {
  claimant_path: string[];
  clbid: string;
  crsid: string;
  value: ICourseRule;
};

type ClaimList = {
  claim: Claim;
  claimant_path: string[];
};

type Operator = "EqualTo" | "GreaterThanOrEqualTo";

export type WhereClauseT =
  | { type: "single-clause"; operator: Operator; key: string; expected: any }
  | { type: "and-clause"; children: WhereClauseT[] }
  | { type: "or-clause"; children: WhereClauseT[] };

export type EvaluatedRequirement = {
  audited_by?: string;
  contract: boolean;
  message: string;
  name: string;
  result: EvaluationResultT;
  saves: {};
  ok: boolean;
  claims: ClaimList[];
  rank: number;
  type: "requirement";
};

export type Course = {
  clbid: string;
  course: string;
  credits: number;
  gereqs: [];
  grade: string;
  graded: string;
  incomplete: false;
  is_repeat: false;
  lab: false;
  name: string;
  number: string;
  section: string;
  semester?: number;
  subjects: string[];
  term: number | { year: number; semester: number };
  transcript_code: string;
  year?: number;
};
