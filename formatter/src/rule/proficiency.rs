use crate::path::Path;
use crate::rule::CourseRule;
use crate::rule::RuleStatus;
use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ProficiencyRule {
    pub status: RuleStatus,
    pub path: Path,
    pub rank: String,
    pub max_rank: String,
    pub proficiency: String,
    pub course: Option<CourseRule>,
}

impl ToProse for ProficiencyRule {
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

        write!(f, "{:?} ", self.status)?;

        writeln!(f)?;

        if let Some(course_rule) = &self.course {
            course_rule.to_prose(f, student, options, indent + 1)?;
        }

        writeln!(f)
    }
}

impl crate::to_csv::ToCsv for ProficiencyRule {
    fn get_record(
        &self,
        student: &Student,
        options: &crate::to_csv::CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)> {
        let is_waived = is_waived || self.status.is_waived();

        let header = self.proficiency.clone();

        if let Some(course_rule) = &self.course {
            let record = course_rule.get_record(student, options, is_waived);
            return vec![(header, record[0].1.clone())];
        }

        let body = if is_waived {
            String::from("<waived>")
        } else if self.status == RuleStatus::Empty {
            String::from(" ")
        } else {
            format!("{:?}", self.status)
        };

        vec![(header, body)]
    }
}
