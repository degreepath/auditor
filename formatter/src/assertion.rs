use crate::filter_predicate::CompoundPredicate;
use crate::operator::Operator;
use crate::path::Path;
use crate::predicate_expression::{DynamicPredicateExpression, StaticPredicateExpression};
use crate::rule::query::DataType;
use crate::rule::RuleStatus;
use crate::student::Course;
use crate::student::{ClassLabId, Student};
use crate::to_prose::{ProseOptions, ToProse};
use crate::to_record::{Cell, Record, RecordOptions, RecordStatus, ToRecord};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::fmt::Display;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum AssertionKey {
    #[serde(rename = "count(courses)")]
    CountCourses,
    #[serde(rename = "count(distinct_courses)")]
    CountDistinctCourses,
    #[serde(rename = "count(terms)")]
    CountTerms,
    #[serde(rename = "count(terms_from_most_common_course_by_name)")]
    CountTermsFromMostCommonCourseByName,
    #[serde(rename = "count(terms_from_most_common_course)")]
    CountTermsFromMostCommonCourse,
    #[serde(rename = "count(performances)")]
    CountPerformances,
    #[serde(rename = "count(recitals)")]
    CountRecitals,
    #[serde(rename = "count(subjects)")]
    CountSubjects,
    #[serde(rename = "count(areas)")]
    CountAreas,
    #[serde(rename = "count(religion_traditions)")]
    CountReligionTraditions,
    #[serde(rename = "count(intlr_regions)")]
    CountInternationalRelationsRegions,
    #[serde(rename = "count(math_perspectives)")]
    CountMathPerspectives,
    #[serde(rename = "sum(credits)")]
    SumCredits,
    #[serde(rename = "sum(credits_from_single_subject)")]
    SumCreditsFromSingleSubject,
    #[serde(rename = "average(grades)")]
    AverageGrades,
}

impl Display for AssertionKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let output = match self {
            AssertionKey::CountAreas => "count/areas",
            AssertionKey::CountCourses => "count/classes",
            AssertionKey::CountDistinctCourses => "count/distinct-courses",
            AssertionKey::CountTerms => "count/terms",
            AssertionKey::CountTermsFromMostCommonCourse => "count/terms-from-most-common-course",
            AssertionKey::CountTermsFromMostCommonCourseByName => {
                "count/terms-from-most-common-course-by-name"
            }
            AssertionKey::CountPerformances => "count/performances",
            AssertionKey::CountRecitals => "count/recitals",
            AssertionKey::CountSubjects => "count/subjects",
            AssertionKey::CountInternationalRelationsRegions => "count/regions",
            AssertionKey::CountMathPerspectives => "count/perspectives",
            AssertionKey::CountReligionTraditions => "count/religions-traditions",
            AssertionKey::SumCredits => "sum/credits",
            AssertionKey::SumCreditsFromSingleSubject => "sum/credits-from-single-subject",
            AssertionKey::AverageGrades => "average/grades",
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

impl ToRecord for Assertion {
    fn get_row(&self, student: &Student, options: &RecordOptions, is_waived: bool) -> Vec<Record> {
        match self {
            Assertion::Rule(r) => r.get_row(student, options, is_waived),
            Assertion::Conditional(r) => r.get_row(student, options, is_waived),
            Assertion::DynamicConditional(r) => r.get_row(student, options, is_waived),
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

    pub fn is_course_or_credit(&self) -> bool {
        match self {
            Assertion::Rule(r) => r.is_course_or_credit(),
            Assertion::Conditional(r) => r.is_course_or_credit(),
            Assertion::DynamicConditional(r) => r.is_course_or_credit(),
        }
    }

    pub fn is_at_least(&self) -> bool {
        match self {
            Assertion::Rule(r) => r.is_at_least(),
            Assertion::Conditional(r) => r.is_at_least(),
            Assertion::DynamicConditional(r) => r.is_at_least(),
        }
    }

    pub fn get_size(&self) -> usize {
        match self {
            Assertion::Rule(r) => r.get_size(),
            Assertion::Conditional(r) => r.get_size(),
            Assertion::DynamicConditional(r) => r.get_size(),
        }
    }
}

impl ToRecord for AssertionRule {
    fn get_row(&self, student: &Student, _options: &RecordOptions, is_waived: bool) -> Vec<Record> {
        let mut row: Vec<Record> = vec![];

        let _is_waived = is_waived || self.status.is_waived();

        let statement = match &self.key {
            AssertionKey::CountAreas => "areas",
            AssertionKey::CountCourses => "courses",
            AssertionKey::CountDistinctCourses => "distinct courses",
            AssertionKey::CountPerformances => "performances",
            AssertionKey::CountRecitals => "recitals",
            AssertionKey::CountSubjects => "subjects",
            AssertionKey::CountTerms => "terms",
            AssertionKey::CountTermsFromMostCommonCourse => "terms from the most common course",
            AssertionKey::CountTermsFromMostCommonCourseByName => {
                "terms from the most common course, by name"
            }
            AssertionKey::SumCredits => "credits",
            AssertionKey::SumCreditsFromSingleSubject => "credits from a single subject",
            AssertionKey::AverageGrades => "grade",
            AssertionKey::CountReligionTraditions => "religious traditions",
            AssertionKey::CountInternationalRelationsRegions => "regions",
            AssertionKey::CountMathPerspectives => "perspectives",
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

        let sigil = if self.status.is_passing() {
            "✓"
        } else {
            "✗"
        };
        let resolved = self.resolved.clone().unwrap_or("0".into());
        let remaining_v = match self.operator {
            Operator::GreaterThanOrEqualTo => {
                let remain =
                    self.expected.parse::<i32>().unwrap() - resolved.parse::<i32>().unwrap();
                format!("{} remaining", remain)
            }
            Operator::NotEqualTo
            | Operator::EqualTo
            | Operator::In
            | Operator::NotIn
            | Operator::GreaterThan
            | Operator::LessThanOrEqualTo
            | Operator::LessThan => format!(
                "{r} {o} {e}",
                r = resolved,
                o = self.operator,
                e = self.expected
            ),
        };
        let leader = format!("{s} {r}", s = sigil, r = remaining_v);

        let courses = self
            .get_clbids()
            .iter()
            .map(|clbid| {
                student.get_class_by_clbid(&clbid).expect(
                    format!(
                        "expected stnum({}) to have clbid({})",
                        &student.stnum,
                        clbid.clbid(),
                    )
                    .as_str(),
                )
            })
            .collect::<Vec<_>>();

        if courses.is_empty() {
            row.push(Record {
                title: header,
                subtitle: None,
                status: RecordStatus::Empty,
                content: vec![Cell::Text(leader)],
            });
        } else {
            let (ip_courses, done_courses): (Vec<&Course>, Vec<&Course>) =
                courses.iter().partition(|c| c.is_in_progress());

            row.push(Record {
                title: header.clone(),
                subtitle: Some("status".to_string()),
                status: self.status,
                content: vec![Cell::Text(leader)],
            });

            row.push(Record {
                title: header.clone(),
                subtitle: Some("completed".to_string()),
                status: self.status,
                content: if done_courses.is_empty() {
                    vec![]
                } else {
                    vec![Cell::DoneCourses(
                        done_courses.into_iter().cloned().collect(),
                    )]
                },
            });

            row.push(Record {
                title: header.clone(),
                subtitle: Some("in-progress".to_string()),
                status: self.status,
                content: if ip_courses.is_empty() {
                    vec![]
                } else {
                    vec![Cell::InProgressCourses(
                        ip_courses.into_iter().cloned().collect(),
                    )]
                },
            });
        };

        row
    }

    fn get_requirements(&self) -> Vec<String> {
        vec![]
    }
}

#[allow(dead_code)]
impl AssertionRule {
    pub fn get_size(&self) -> usize {
        match self.key {
            AssertionKey::CountAreas => self.expected.parse().unwrap(),
            AssertionKey::CountCourses => self.expected.parse().unwrap(),
            AssertionKey::CountDistinctCourses => self.expected.parse().unwrap(),
            AssertionKey::CountTerms => self.expected.parse().unwrap(),
            AssertionKey::CountTermsFromMostCommonCourse => self.expected.parse().unwrap(),
            AssertionKey::CountTermsFromMostCommonCourseByName => self.expected.parse().unwrap(),
            AssertionKey::CountPerformances => self.expected.parse().unwrap(),
            AssertionKey::CountRecitals => self.expected.parse().unwrap(),
            AssertionKey::CountSubjects => self.expected.parse().unwrap(),
            AssertionKey::CountReligionTraditions => self.expected.parse().unwrap(),
            AssertionKey::CountInternationalRelationsRegions => self.expected.parse().unwrap(),
            AssertionKey::CountMathPerspectives => self.expected.parse().unwrap(),
            AssertionKey::SumCredits | AssertionKey::SumCreditsFromSingleSubject => {
                let as_float: f64 = self.expected.parse().unwrap();
                let as_int: usize = as_float.round() as usize;
                if as_float > (as_int as f64) {
                    as_int + 1
                } else {
                    as_int
                }
            }
            AssertionKey::AverageGrades => {
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

    pub fn is_course_or_credit(&self) -> bool {
        match self.key {
            AssertionKey::CountCourses => true,
            AssertionKey::CountDistinctCourses => true,
            AssertionKey::SumCredits => true,
            AssertionKey::SumCreditsFromSingleSubject => false,
            AssertionKey::CountTerms => false,
            AssertionKey::CountTermsFromMostCommonCourse => false,
            AssertionKey::CountTermsFromMostCommonCourseByName => false,
            AssertionKey::CountPerformances => false,
            AssertionKey::CountRecitals => false,
            AssertionKey::CountSubjects => false,
            AssertionKey::CountAreas => false,
            AssertionKey::AverageGrades => false,
            AssertionKey::CountReligionTraditions => false,
            AssertionKey::CountInternationalRelationsRegions => false,
            AssertionKey::CountMathPerspectives => false,
        }
    }

    pub fn is_at_least(&self) -> bool {
        match self.operator {
            Operator::GreaterThanOrEqualTo => true,
            Operator::EqualTo => true,
            Operator::GreaterThan => true,
            Operator::NotEqualTo => false,
            Operator::In => false,
            Operator::NotIn => false,
            Operator::LessThan => false,
            Operator::LessThanOrEqualTo => false,
        }
    }
}

impl ToRecord for ConditionalAssertion {
    fn get_row(&self, student: &Student, options: &RecordOptions, is_waived: bool) -> Vec<Record> {
        let if_true = self.when_true.get_row(student, options, is_waived);
        let if_false = if let Some(b) = &self.when_false {
            b.get_row(student, options, is_waived)
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

    pub fn is_course_or_credit(&self) -> bool {
        if self.when_true.is_course_or_credit() {
            return true;
        }
        match &self.when_false {
            Some(when_false) => when_false.is_course_or_credit(),
            None => false,
        }
    }

    pub fn is_at_least(&self) -> bool {
        if self.when_true.is_at_least() {
            return true;
        }
        match &self.when_false {
            Some(when_false) => when_false.is_at_least(),
            None => false,
        }
    }
}

impl ToRecord for DynamicConditionalAssertion {
    fn get_row(&self, student: &Student, options: &RecordOptions, is_waived: bool) -> Vec<Record> {
        self.when_true.get_row(student, options, is_waived)
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

    pub fn is_course_or_credit(&self) -> bool {
        self.when_true.is_course_or_credit()
    }

    pub fn is_at_least(&self) -> bool {
        self.when_true.is_at_least()
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
