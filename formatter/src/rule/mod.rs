use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use crate::to_record::{Record, RecordOptions, ToRecord};
use serde::{Deserialize, Serialize};

pub mod conditional;
pub mod count;
pub mod course;
pub mod proficiency;
pub mod query;
pub mod requirement;

use conditional::ConditionalRule;
use count::CountRule;
use course::CourseRule;
use proficiency::ProficiencyRule;
use query::QueryRule;
use requirement::Requirement;

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(tag = "type")]
pub enum Rule {
    #[serde(rename = "count")]
    Count(CountRule),
    #[serde(rename = "proficiency")]
    Proficiency(ProficiencyRule),
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
            Rule::Proficiency(r) => r.to_prose(f, student, options, indent),
        }
    }
}

impl ToRecord for Rule {
    fn get_row(&self, student: &Student, options: &RecordOptions, is_waived: bool) -> Vec<Record> {
        match self {
            Rule::Count(r) => r.get_row(student, options, is_waived),
            Rule::Course(r) => r.get_row(student, options, is_waived),
            Rule::Requirement(r) => r.get_row(student, options, is_waived),
            Rule::Query(r) => r.get_row(student, options, is_waived),
            Rule::Conditional(r) => r.get_row(student, options, is_waived),
            Rule::Proficiency(r) => r.get_row(student, options, is_waived),
        }
    }

    fn get_requirements(&self) -> Vec<String> {
        match self {
            Rule::Count(r) => r.get_requirements(),
            Rule::Course(r) => r.get_requirements(),
            Rule::Requirement(r) => r.get_requirements(),
            Rule::Query(r) => r.get_requirements(),
            Rule::Conditional(r) => r.get_requirements(),
            Rule::Proficiency(r) => r.get_requirements(),
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
            Rule::Proficiency(r) => &r.status,
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone, Eq, PartialEq, Copy)]
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
    #[serde(rename = "failed-invariant")]
    FailedInvariant,
}

impl RuleStatus {
    pub fn is_passing(&self) -> bool {
        match self {
            RuleStatus::Done => true,
            RuleStatus::Waived => true,
            RuleStatus::PendingCurrent => true,
            RuleStatus::NeedsMoreItems => false,
            RuleStatus::PendingRegistered => false,
            RuleStatus::PendingApproval => false,
            RuleStatus::Empty => false,
            RuleStatus::FailedInvariant => false,
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
            RuleStatus::FailedInvariant => false,
        }
    }
}
