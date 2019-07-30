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

export interface AssertionClauseT {
  expected: number;
  expected_verbatim: number | "$senior-year" | "$matriculation-year";
  where: WhereClauseT | null;
  key: "count(courses)" | "sum(credits)";
  operator: Operator;
  source: string;
  type: "single-clause";
}

export interface IAssertionT {
  type: "assertion";
  status: "skip";
  state: "rule";
  rank: number;
  ok: boolean;
  assertion: WhereClauseT;
  where: null | WhereClauseT;
}

export interface IFromRule extends BaseRule {
  type: "from";
  source_type: "courses" | "areas" | string;
  source_repeats: "all" | "first";
  source: "student";
  claims?: ClaimList[];
  failures?: ClaimList[];
  limit: Limit[];
  where: WhereClauseT;
  assertions: IAssertionT[];
  allow_claimed: boolean;
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

type Operator = "EqualTo" | "GreaterThanOrEqualTo" | "GreaterThan" | "In";

export type WhereClauseT =
  | {
      type: "single-clause";
      operator: Operator;
      key: string;
      expected: any;
      expected_verbatim: any;
      resolved_with?: number;
      resolved_items?: any[];
      result?: boolean;
    }
  | { type: "and-clause"; children: WhereClauseT[] }
  | { type: "or-clause"; children: WhereClauseT[] };

export type EvaluatedRequirement = {
  audited_by: null | string;
  contract: boolean;
  message: null | string;
  name: string;
  result: EvaluationResultT;
  ok: boolean;
  claims: ClaimList[];
  rank: number;
  type: "requirement";
  requirements: { [key: string]: EvaluatedRequirement };
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

export type Transcript = ReadonlyMap<string, Course>;
