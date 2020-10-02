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
    pub code: String,
    pub degree: Option<String>,
    pub gpa: String,
    pub kind: String,
    pub limit: Vec<Limit>,
    pub max_rank: String,
    pub name: String,
    pub ok: bool,
    pub path: Path,
    pub rank: String,
    pub result: Box<Rule>,
    pub status: RuleStatus,
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
        is_waived: bool,
    ) -> Vec<(String, String)> {
        let mut row = vec![(String::from("student"), student.stnum.clone())];

        row.append(&mut self.result.get_record(student, options, is_waived));

        row
    }

    fn get_requirements(&self) -> Vec<String> {
        self.result.get_requirements()
    }
}
