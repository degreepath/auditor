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

use crate::to_record::{Record, RecordOptions, RecordStatus, ToRecord};
impl ToRecord for ProficiencyRule {
    fn get_row(&self, student: &Student, options: &RecordOptions, is_waived: bool) -> Vec<Record> {
        let is_waived = is_waived || self.status.is_waived();

        let header = self.proficiency.clone();

        if let Some(course_rule) = &self.course {
            let mut row = course_rule.get_row(student, options, is_waived);
            if row.len() != 1 {
                panic!("proficiency rule got more than one course record");
            }
            row[0].title = header;
            return row;
        }

        let (body, status) = if is_waived {
            (None, RecordStatus::Waived)
        } else if self.status == RuleStatus::Empty {
            (None, RecordStatus::Empty)
        } else {
            (None, self.status)
        };

        let body = if let Some(body) = body {
            vec![body]
        } else {
            vec![]
        };

        vec![Record {
            title: header,
            subtitle: None,
            status: status,
            content: body,
        }]
    }

    fn get_requirements(&self) -> Vec<String> {
        vec![]
    }
}
