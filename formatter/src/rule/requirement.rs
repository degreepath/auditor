use crate::path::Path;
use crate::rule::{Rule, RuleStatus};
use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Requirement {
    pub contract: bool,
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

impl crate::to_csv::ToCsv for Requirement {
    fn get_record(
        &self,
        student: &Student,
        options: &crate::to_csv::CsvOptions,
    ) -> Vec<(String, String)> {
        if self.path == &["$", "%Common Requirements"] {
            return vec![];
        }

        let mut record = vec![];

        if let Some(result) = &self.result {
            for (column, value) in result.get_record(student, options) {
                record.push((format!("{} > {}", self.name, column), value));
            }
        }

        record
    }
}
