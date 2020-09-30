use crate::assertion::Assertion;
use crate::claim::Claim;
use crate::filter_predicate::CompoundPredicate;
use crate::limit::Limit;
use crate::path::Path;
use crate::rule::RuleStatus;
use crate::student::{ClassLabId, Course, Student};
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum QuerySource {
    #[serde(rename = "courses")]
    Courses,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum DataType {
    #[serde(rename = "course")]
    Course,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct QueryRule {
    pub allow_claimed: bool,
    pub assertions: Vec<Assertion>,
    pub claims: Vec<Claim>,
    #[serde(rename = "data-type")]
    pub data_type: DataType,
    pub failures: Vec<Claim>,
    pub inserted: Vec<ClassLabId>,
    pub limit: Vec<Limit>,
    pub max_rank: String,
    pub path: Path,
    pub rank: String,
    pub source: QuerySource,
    pub status: RuleStatus,
    #[serde(rename = "where")]
    pub filter: Option<CompoundPredicate>,
}

impl QueryRule {
    #[allow(dead_code)]
    pub fn get_claimed_courses<'a>(&self, student: &'a Student) -> Vec<&'a Course> {
        let mut known_clbids: BTreeSet<ClassLabId> = BTreeSet::new();

        known_clbids.extend(self.claims.iter().map(|clm| clm.clbid.clone()));
        known_clbids.extend(self.assertions.iter().flat_map(|a| a.get_clbids()));

        known_clbids
            .iter()
            .map(|clbid| student.get_class_by_clbid(&clbid).unwrap())
            .collect()
    }

    #[allow(dead_code)]
    pub fn get_largest_count(&self) -> usize {
        self.assertions
            .iter()
            .map(|a| a.get_size())
            .max()
            .unwrap_or(0)
    }
}

impl ToProse for QueryRule {
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

        if options.show_ranks {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(
                f,
                "rank({2}): {0} of {1}",
                self.rank,
                self.max_rank,
                if self.status.is_passing() { "t" } else { "f" }
            )?;
        };

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "status: {:?}", self.status)?;

        if let Some(filter) = &self.filter {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "Given courses matching")?;
            write!(f, "{}", " ".repeat((indent + 1) * 4))?;
            filter.to_prose(f, student, options, indent + 1)?;
            writeln!(f)?;
        }

        if !self.limit.is_empty() {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "Subject to these limits:")?;
            for l in &self.limit {
                write!(f, "{}", " ".repeat(indent * 4))?;
                write!(f, "- ")?;
                l.to_prose(f, student, options, indent)?;
                writeln!(f)?;
            }
        }

        if !self.claims.is_empty() {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "Matching courses:")?;

            for clm in &self.claims {
                if let Some(course) = student.get_class_by_clbid(&clm.clbid) {
                    write!(f, "{}", " ".repeat((indent + 1) * 4))?;
                    write!(f, "- ")?;
                    if self.inserted.contains(&clm.clbid) {
                        write!(f, "[ins] ")?;
                    };
                    write!(f, "{} ", course.calculate_symbol(&self.status))?;
                    writeln!(f, "{}", course.verbose())?;
                } else {
                    writeln!(f, "   !!!!! \"!!!!!\" ({:?})", clm.clbid)?;
                    continue;
                }
            }
        }

        if !self.failures.is_empty() {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "Pre-claimed courses which cannot be re-claimed:")?;
            for clm in &self.failures {
                write!(f, "{}", " ".repeat((indent + 1) * 4))?;
                if let Some(course) = student.get_class_by_clbid(&clm.clbid) {
                    writeln!(f, "- {}", course.verbose())?;
                } else {
                    writeln!(f, "- {:?}", clm.clbid)?;
                    continue;
                }
            }
        }

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "There must be:")?;
        for (i, a) in self.assertions.iter().enumerate() {
            write!(f, "{}", " ".repeat((indent + 1) * 4))?;
            writeln!(f, "{}.", i + 1)?;
            a.to_prose(f, student, options, indent + 2)?;
            writeln!(f)?;
        }

        Ok(())
    }
}

impl crate::to_csv::ToCsv for QueryRule {
    fn get_record(
        &self,
        student: &Student,
        options: &crate::to_csv::CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)> {
        let mut record: Vec<(String, String)> = Vec::new();

        let is_waived = is_waived || self.status.is_waived();

        for assertion in &self.assertions {
            record.extend(
                assertion
                    .get_record(student, options, is_waived)
                    .into_iter(),
            );
        }

        record
    }
}
