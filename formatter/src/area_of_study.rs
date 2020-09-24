use crate::limit::Limit;
use crate::path::Path;
use crate::rule::{Rule, RuleStatus};
use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AreaOfStudy {
    #[serde(rename = "type")]
    pub _type: String,
    pub status: RuleStatus,
    pub result: Box<Rule>,
    pub rank: String,
    pub path: Path,
    pub ok: bool,
    pub name: String,
    pub max_rank: String,
    pub limit: Vec<Limit>,
    pub kind: String,
    pub gpa: String,
    pub degree: String,
    pub code: String,
}

impl ToProse for AreaOfStudy {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        student: &Student,
        options: &ProseOptions,
        indent: usize,
    ) -> std::fmt::Result {
        writeln!(
            f,
            "\"{name}\" audit status: {status:?} (rank {rank} of {max_rank}; gpa: {gpa})",
            name = self.name,
            status = self.status,
            rank = self.rank,
            max_rank = self.max_rank,
            gpa = self.gpa
        )?;

        if !self.limit.is_empty() {
            write!(f, "{}", " ".repeat(indent * 4))?;
            writeln!(f, "Subject to these limits:")?;
            for l in &self.limit {
                write!(f, "{}", " ")?;
                l.to_prose(f, student, options, indent + 1)?;
                writeln!(f)?;
            }
        };

        self.result.to_prose(f, student, options, indent)?;

        Ok(())
    }
}

impl crate::to_csv::ToCsv for AreaOfStudy {
    fn get_record(
        &self,
        student: &Student,
        options: &crate::to_csv::CsvOptions,
    ) -> Vec<(String, String)> {
        let mut row = vec![(String::from("student"), student.stnum.clone())];

        row.append(&mut self.result.get_record(student, options));

        row
    }
}
