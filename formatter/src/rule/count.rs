use crate::audit::AuditResult;
use crate::path::Path;
use crate::rule::{Rule, RuleStatus};
use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CountRule {
    pub count: usize,
    pub audit_status: RuleStatus,
    pub audit: Vec<AuditResult>,
    pub items: Vec<Box<Rule>>,
    pub max_rank: String,
    pub path: Path,
    pub rank: String,
    pub status: RuleStatus,
}

impl ToProse for CountRule {
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

        write!(f, "{}", " ".repeat(indent * 4))?;
        let size = self.items.len();

        if self.count == 1 && size == 2 {
            write!(f, "either of (these 2)")?;
        } else if self.count == 2 && size == 2 {
            write!(f, "both of (these 2)")?;
        } else if (self.count as usize) == size {
            write!(f, "all of (these {})", size)?;
        } else if self.count == 2 {
            write!(f, "any of (these {})", size)?;
        } else {
            write!(f, "at least {} of {}", self.count, size)?;
        }

        let ok_count = self
            .items
            .iter()
            .filter(|r| r.status().is_passing())
            .count();

        write!(f, " (ok: {}, need: {})", ok_count, self.count)?;

        writeln!(f)?;

        if !self.audit.is_empty() {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(
                f,
                "This requirement has a post-audit [status={:?}]",
                self.audit_status
            )?;

            write!(f, "{}", " ".repeat((indent + 1) * 4))?;
            writeln!(f, "There must be:")?;

            for (i, a) in self.audit.iter().enumerate() {
                writeln!(f, "{}.", i + 1)?;
                a.to_prose(f, student, options, indent + 2)?;
            }

            writeln!(f)?;
        }

        for (i, r) in self.items.iter().enumerate() {
            write!(f, "{}", " ".repeat((indent + 1) * 4))?;
            writeln!(f, "{}.", i + 1)?;

            r.to_prose(f, student, options, indent + 2)?;

            if size != 2 && i < self.items.len() - 1 {
                writeln!(f)?;
            }
        }

        Ok(())
    }
}

impl crate::to_csv::ToCsv for CountRule {
    fn get_record(
        &self,
        student: &Student,
        options: &crate::to_csv::CsvOptions,
    ) -> Vec<(String, String)> {
        let mut record: Vec<(String, String)> = Vec::new();

        if self.count == 1 {
            let text = format!("#1");
            let item = self.items.iter().find(|r| r.status().is_passing());

            match item {
                Some(item) => {
                    for (column, value) in item.get_record(student, options) {
                        record.push((format!("{} > {}", text.clone(), column), value));
                    }
                }
                _ => {
                    record.push((format!("{} > {}", text.clone(), ""), "".into()));
                }
            }
        } else {
            for (i, item) in self.items.iter().enumerate() {
                let text = format!("#{}", i + 1);
                for (column, value) in item.get_record(student, options) {
                    record.push((format!("{} > {}", text.clone(), column), value));
                }
            }
        }

        record
    }
}
