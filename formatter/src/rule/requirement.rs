use crate::path::Path;
use crate::rule::{Rule, RuleStatus};
use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Requirement {
    // pub contract: bool,
    pub is_audited: bool,
    pub max_rank: String,
    pub message: Option<String>,
    pub name: String,
    pub path: Path,
    pub rank: String,
    pub result: Option<Box<Rule>>,
    pub status: RuleStatus,
}

impl ToProse for Requirement {
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
        };

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "status: {:?}", self.status)?;

        write!(f, "{}", " ".repeat(indent * 4))?;
        writeln!(f, "Requirement({})", self.name)?;

        if self.is_audited {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "is manually audited")?;
        }

        if let Some(result) = &self.result {
            result.to_prose(f, student, options, indent + 1)?;
        }

        Ok(())
    }
}

use crate::to_record::{Record, RecordOptions, ToRecord};
impl ToRecord for Requirement {
    fn get_row(&self, student: &Student, options: &RecordOptions, is_waived: bool) -> Vec<Record> {
        if self.path == &["$", "%Common Requirements"] {
            return vec![];
        }

        let is_waived = is_waived || self.status.is_waived();

        let mut row = vec![];

        if let Some(result) = &self.result {
            row.extend(
                result
                    .get_row(student, options, is_waived)
                    .iter()
                    .map(|record| record.with_title(&format!("{} → {}", self.name, &record.title))),
            );
        }

        row
    }

    fn get_requirements(&self) -> Vec<String> {
        let mut initial = vec![self.name.clone()];
        match &self.result {
            Some(r) => {
                initial.extend(r.get_requirements().into_iter());
            }
            None => {}
        }
        initial
    }
}
