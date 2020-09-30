use crate::student::Student;
use crate::to_csv::{CsvOptions, ToCsv};
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

pub mod conditional;
pub mod count;
pub mod course;
pub mod query;
pub mod requirement;

use conditional::ConditionalRule;
use count::CountRule;
use course::CourseRule;
use query::QueryRule;
use requirement::Requirement;

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(tag = "type")]
pub enum Rule {
    #[serde(rename = "count")]
    Count(CountRule),
    #[serde(rename = "course")]
    Course(CourseRule),
    #[serde(rename = "requirement")]
    Requirement(Requirement),
    #[serde(rename = "query")]
    Query(QueryRule),
    #[serde(rename = "conditional")]
    Conditional(ConditionalRule),
}

impl ToProse for Rule {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        match self {
            Rule::Count(r) => r.to_prose(f, student, options, indent),
            Rule::Course(r) => r.to_prose(f, student, options, indent),
            Rule::Requirement(r) => r.to_prose(f, student, options, indent),
            Rule::Query(r) => r.to_prose(f, student, options, indent),
            Rule::Conditional(r) => r.to_prose(f, student, options, indent),
        }
    }
}

impl ToCsv for Rule {
    fn get_record(
        &self,
        student: &Student,
        options: &CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)> {
        match self {
            Rule::Count(r) => r.get_record(student, options, is_waived),
            Rule::Course(r) => r.get_record(student, options, is_waived),
            Rule::Requirement(r) => r.get_record(student, options, is_waived),
            Rule::Query(r) => r.get_record(student, options, is_waived),
            Rule::Conditional(r) => r.get_record(student, options, is_waived),
        }
    }
}

impl Rule {
    fn status(&self) -> &RuleStatus {
        match self {
            Rule::Count(r) => &r.status,
            Rule::Course(r) => &r.status,
            Rule::Requirement(r) => &r.status,
            Rule::Query(r) => &r.status,
            Rule::Conditional(r) => &r.status,
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone, Eq, PartialEq)]
pub enum RuleStatus {
    #[serde(rename = "done")]
    Done,
    #[serde(rename = "waived")]
    Waived,
    #[serde(rename = "needs-more-items")]
    NeedsMoreItems,
    #[serde(rename = "pending-current")]
    PendingCurrent,
    #[serde(rename = "pending-registered")]
    PendingRegistered,
    #[serde(rename = "pending-approval")]
    PendingApproval,
    #[serde(rename = "empty")]
    Empty,
}

impl RuleStatus {
    pub fn is_passing(&self) -> bool {
        match self {
            RuleStatus::Done | RuleStatus::Waived | RuleStatus::PendingCurrent => true,
            RuleStatus::NeedsMoreItems => false,
            RuleStatus::PendingRegistered => false,
            RuleStatus::PendingApproval => false,
            RuleStatus::Empty => false,
        }
    }

    pub fn is_waived(&self) -> bool {
        match self {
            RuleStatus::Waived => true,
            RuleStatus::Done => false,
            RuleStatus::NeedsMoreItems => false,
            RuleStatus::PendingRegistered => false,
            RuleStatus::PendingCurrent => false,
            RuleStatus::PendingApproval => false,
            RuleStatus::Empty => false,
        }
    }
}
