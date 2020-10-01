use crate::filter_predicate::CompoundPredicate;
use crate::operator::Operator;
use crate::path::Path;
use crate::predicate_expression::{DynamicPredicateExpression, StaticPredicateExpression};
use crate::rule::query::DataType;
use crate::rule::RuleStatus;
use crate::student::{ClassLabId, Student};
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::fmt::Display;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum AssertionKey {
    #[serde(rename = "count(courses)")]
    CountCourses,
    #[serde(rename = "count(terms)")]
    CountTerms,
    #[serde(rename = "count(performances)")]
    CountPerformances,
    #[serde(rename = "count(recitals)")]
    CountRecitals,
    #[serde(rename = "count(subjects)")]
    CountSubjects,
    #[serde(rename = "sum(credits)")]
    SumCredits,
}

impl Display for AssertionKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let output = match self {
            AssertionKey::CountCourses => "count/classes",
            AssertionKey::CountTerms => "count/terms",
            AssertionKey::CountPerformances => "count/performances",
            AssertionKey::CountRecitals => "count/recitals",
            AssertionKey::CountSubjects => "count/subjects",
            AssertionKey::SumCredits => "sum/credits",
        };

        f.write_str(output)
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(tag = "type")]
pub enum Assertion {
    #[serde(rename = "assertion")]
    Rule(AssertionRule),
    #[serde(rename = "assertion--if")]
    Conditional(ConditionalAssertion),
    #[serde(rename = "assertion--when")]
    DynamicConditional(DynamicConditionalAssertion),
}

impl crate::to_csv::ToCsv for Assertion {
    fn get_record(
        &self,
        student: &Student,
        options: &crate::to_csv::CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)> {
        match self {
            Assertion::Rule(r) => r.get_record(student, options, is_waived),
            Assertion::Conditional(r) => r.get_record(student, options, is_waived),
            Assertion::DynamicConditional(r) => r.get_record(student, options, is_waived),
        }
    }

    fn get_requirements(&self) -> Vec<String> {
        vec![]
    }
}

impl Assertion {
    #[allow(dead_code)]
    fn get_resolved_items(&self) -> String {
        match self {
            Assertion::Rule(r) => {
                if let Some(_) = r.resolved {
                    let mut items = r.resolved_items.clone();
                    items.sort();
                    items.join(", ")
                } else {
                    String::from("")
                }
            }
            Assertion::Conditional(_r) => String::from("( conditional assertion )"),
            Assertion::DynamicConditional(_r) => String::from("( dyn conditional assertion )"),
        }
    }

    #[allow(dead_code)]
    pub fn get_clbids(&self) -> Vec<ClassLabId> {
        match self {
            Assertion::Rule(r) => r.get_clbids(),
            Assertion::Conditional(r) => r.get_clbids(),
            Assertion::DynamicConditional(r) => r.get_clbids(),
        }
    }

    pub fn get_resolved_clbids(&self) -> Vec<ClassLabId> {
        match self {
            Assertion::Rule(r) => {
                let mut items = r.resolved_clbids.clone();
                items.sort();
                items
            }
            Assertion::Conditional(_r) => unimplemented!(),
            Assertion::DynamicConditional(_r) => unimplemented!(),
        }
    }

    #[allow(dead_code)]
    pub fn get_size(&self) -> usize {
        match self {
            Assertion::Rule(r) => r.get_size(),
            Assertion::Conditional(r) => r.get_size(),
            Assertion::DynamicConditional(r) => r.get_size(),
        }
    }
}

impl crate::to_csv::ToCsv for AssertionRule {
    fn get_record(
        &self,
        student: &Student,
        _options: &crate::to_csv::CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)> {
        let _is_waived = is_waived || self.status.is_waived();

        let statement = match &self.key {
            AssertionKey::CountCourses => "courses",
            AssertionKey::CountPerformances => "performances",
            AssertionKey::CountRecitals => "recitals",
            AssertionKey::CountSubjects => "subjects",
            AssertionKey::CountTerms => "terms",
            AssertionKey::SumCredits => "credits",
        };

        let header = match self.operator {
            Operator::EqualTo => format!("needs … {}", statement),
            Operator::NotEqualTo => format!("not … {}", statement),
            Operator::In => unimplemented!(),
            Operator::NotIn => unimplemented!(),
            Operator::LessThan => format!("fewer than … {}", statement),
            Operator::LessThanOrEqualTo => format!("at most … {}", statement),
            Operator::GreaterThan => format!("more than … {}", statement),
            Operator::GreaterThanOrEqualTo => format!("at least … {}", statement),
        };

        // dbg!(&self);

        let sigil = if self.status.is_passing() {
            "✓"
        } else {
            "✗"
        };
        let resolved = self.resolved.clone().unwrap_or("0".into());
        let leader = format!(
            "{s} {r} {o} {e}",
            s = sigil,
            r = resolved,
            o = self.operator,
            e = self.expected
        );

        let courses = self
            .get_clbids()
            .iter()
            .map(|clbid| student.get_class_by_clbid(&clbid).unwrap())
            .map(|c| c.semi_verbose())
            .collect::<Vec<_>>();

        let body = if courses.is_empty() {
            leader
        } else {
            format!("{} → {}", leader, courses.join("; "))
        };

        vec![(header, body)]
    }

    fn get_requirements(&self) -> Vec<String> {
        vec![]
    }
}

#[allow(dead_code)]
impl AssertionRule {
    pub fn get_size(&self) -> usize {
        match self.key {
            AssertionKey::CountCourses => self.expected.parse().unwrap(),
            AssertionKey::CountTerms => self.expected.parse().unwrap(),
            AssertionKey::CountPerformances => self.expected.parse().unwrap(),
            AssertionKey::CountRecitals => self.expected.parse().unwrap(),
            AssertionKey::CountSubjects => self.expected.parse().unwrap(),
            AssertionKey::SumCredits => {
                let as_float: f64 = self.expected.parse().unwrap();
                let as_int: usize = as_float.round() as usize;
                if as_float > (as_int as f64) {
                    as_int + 1
                } else {
                    as_int
                }
            }
        }
    }

    pub fn get_clbids(&self) -> Vec<ClassLabId> {
        let mut set: BTreeSet<ClassLabId> = BTreeSet::new();

        set.extend(self.inserted_clbids.iter().cloned());
        set.extend(self.resolved_clbids.iter().cloned());

        set.iter().cloned().collect()
    }
}

impl crate::to_csv::ToCsv for ConditionalAssertion {
    fn get_record(
        &self,
        student: &Student,
        options: &crate::to_csv::CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)> {
        let if_true = self.when_true.get_record(student, options, is_waived);
        let if_false = if let Some(b) = &self.when_false {
            b.get_record(student, options, is_waived)
        } else {
            vec![]
        };

        vec![if_true, if_false].iter().flatten().cloned().collect()
    }

    fn get_requirements(&self) -> Vec<String> {
        vec![]
    }
}

impl ConditionalAssertion {
    pub fn get_size(&self) -> usize {
        if let Some(f) = &self.when_false {
            std::cmp::max(self.when_true.get_size(), f.get_size())
        } else {
            self.when_true.get_size()
        }
    }

    pub fn get_clbids(&self) -> Vec<ClassLabId> {
        match self.condition.result() {
            Some(true) => self.when_true.get_clbids(),
            Some(false) if self.when_false.is_some() => {
                if let Some(f) = &self.when_false {
                    f.get_clbids()
                } else {
                    vec![]
                }
            }
            Some(false) => vec![],
            None => vec![],
        }
    }
}

impl crate::to_csv::ToCsv for DynamicConditionalAssertion {
    fn get_record(
        &self,
        student: &Student,
        options: &crate::to_csv::CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)> {
        self.when_true.get_record(student, options, is_waived)
    }

    fn get_requirements(&self) -> Vec<String> {
        vec![]
    }
}

impl DynamicConditionalAssertion {
    pub fn get_size(&self) -> usize {
        self.when_true.get_size()
    }

    pub fn get_clbids(&self) -> Vec<ClassLabId> {
        match self.condition.result() {
            Some(true) => self.when_true.get_clbids(),
            _ => vec![],
        }
    }
}

impl ToProse for Assertion {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        match self {
            Assertion::Rule(r) => r.to_prose(f, student, options, indent),
            Assertion::Conditional(r) => r.to_prose(f, student, options, indent),
            Assertion::DynamicConditional(r) => r.to_prose(f, student, options, indent),
        }
    }
}

impl ToProse for AssertionRule {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        if options.show_paths {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "path: {}", self.path)?;
        }

        if options.show_ranks {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(
                f,
                "rank({2}): {0} of {1}",
                self.rank,
                self.max_rank,
                if self.status.is_passing() { "t" } else { "f" }
            )?;
        }

        write!(f, "{}", " ".repeat(indent * 4))?;

        writeln!(f, "status: {:?}", self.status)?;

        write!(f, "{}", " ".repeat(indent * 4))?;

        let resolved_key = if let Some(resolved_with) = &self.resolved {
            format!("key: {} [value: {:?}]", self.key, resolved_with)
        } else {
            format!("key: {}", self.key)
        };

        if self.operator == Operator::EqualTo && self.expected == serde_json::Value::Bool(true) {
            write!(f, "{}", resolved_key)?;
        } else if self.operator == Operator::EqualTo
            && self.expected == serde_json::Value::Bool(false)
        {
            write!(f, "not {}", resolved_key)?;
        } else {
            write!(f, "{} {} {}", resolved_key, self.operator, self.expected)?;
        }

        if let Some(original) = &self.original {
            write!(f, " [via {:?}]", original)?;
        }

        if let Some(label) = &self.label {
            write!(f, " [label: \"{}\"]", label)?;
        }

        writeln!(f)?;

        if let Some(filter) = &self.filter {
            write!(f, "{}", " ".repeat(indent * 4))?;
            write!(f, "where ")?;
            filter.to_prose(f, student, options, indent)?;
            writeln!(f)?;
        }

        let as_enum = Assertion::Rule(self.clone());

        // let resolved_items = get_resolved_items(&as_enum);
        // if !resolved_items.is_empty() {
        //     write!(f, "{}", " ".repeat(indent * 4))?;
        //     writeln!(f, "resolved items: {}", resolved_items)?;
        // }

        let resolved_clbids = as_enum.get_resolved_clbids();
        if !resolved_clbids.is_empty() {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "resolved classes:")?;

            for (i, clbid) in resolved_clbids.iter().enumerate() {
                write!(f, "{}", " ".repeat((indent + 1) * 4))?;
                // let inserted_msg = if self.inserted.contains(&clbid) {
                //     " [ins]"
                // } else {
                //     ""
                // };
                let inserted_msg = "";

                if let Some(course) = student.get_class_by_clbid(&clbid) {
                    writeln!(
                        f,
                        "{:0>2}. {}{} {}",
                        i + 1,
                        inserted_msg,
                        course.calculate_symbol(&self.status),
                        course.verbose()
                    )?;
                } else {
                    writeln!(f, "- {} #{:?}", inserted_msg, clbid)?;
                }
            }
        }

        Ok(())
    }
}

impl ToProse for ConditionalAssertion {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        if options.show_paths {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "path: {}", self.path)?;
        };

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "If: [{}]", self.condition)?;

        let branch = self.condition.result();
        let true_branch = if branch == Some(true) { "t." } else { "" };
        let false_branch = if branch == Some(false) { "f!" } else { "" };

        writeln!(f, "Then ({})", true_branch)?;

        self.when_true.to_prose(f, student, options, indent + 1)?;

        writeln!(f)?;

        writeln!(f, "Else ({})", false_branch)?;

        if let Some(pred) = &self.when_false {
            pred.to_prose(f, student, options, indent + 1)?;
            writeln!(f)?;
        } else {
            write!(f, "do nothing")?;
        }

        Ok(())
    }
}

impl ToProse for DynamicConditionalAssertion {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        if options.show_paths {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "path: {}", self.path)?;
        };

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "If: [{}]", self.condition)?;

        let branch = self.condition.result();
        let true_branch = if branch == Some(true) { "t." } else { "" };
        let false_branch = if branch == Some(false) { "f!" } else { "" };

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "Then ({})", true_branch)?;

        self.when_true.to_prose(f, student, options, indent)?;

        writeln!(f)?;

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "Else ({}): do nothing", false_branch)?;

        Ok(())
    }
}

// TODO: serde rule to convert string|number to a string; use for "original" key

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AssertionRule {
    #[serde(rename = "data-type")]
    pub data_type: DataType,
    pub evaluated: Option<bool>,
    pub expected: String,
    pub inserted_clbids: Vec<ClassLabId>,
    pub key: AssertionKey,
    pub label: Option<String>,
    pub max_rank: String,
    pub message: Option<String>,
    pub operator: Operator,
    pub original: Option<serde_json::Value>,
    pub path: Path,
    pub rank: String,
    pub resolved: Option<String>,
    pub resolved_clbids: Vec<ClassLabId>,
    pub resolved_items: Vec<String>,
    pub status: RuleStatus,
    #[serde(rename = "where")]
    pub filter: Option<CompoundPredicate>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ConditionalAssertion {
    pub path: Path,
    pub condition: StaticPredicateExpression,
    pub when_true: AssertionRule,
    pub when_false: Option<AssertionRule>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DynamicConditionalAssertion {
    pub path: Path,
    pub condition: DynamicPredicateExpression,
    pub when_true: AssertionRule,
}
