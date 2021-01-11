use crate::claim::Claim;
use crate::path::Path;
use crate::rule::RuleStatus;
use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CourseRule {
    pub claims: Vec<Claim>,
    pub status: RuleStatus,
    pub path: Path,
    pub rank: String,
    pub max_rank: String,
    #[serde(deserialize_with = "crate::serde::empty_str_as_none")]
    pub course: Option<String>,
    #[serde(deserialize_with = "crate::serde::empty_str_as_none")]
    pub ap: Option<String>,
    pub institution: Option<String>,
    pub clbid: Option<String>,
    pub grade: Option<String>,
    pub name: Option<String>,
    pub crsid: Option<String>,
}

impl ToProse for CourseRule {
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
        let matched_course = if let Some(claim) = self.claims.get(0) {
            student.get_class_by_clbid(&claim.clbid)
        } else {
            None
        };

        let status = matched_course.map_or("", |c| c.calculate_symbol(&self.status));

        write!(f, "{} ", status)?;

        match (&self.status, matched_course, &self.course, &self.ap) {
            (RuleStatus::Waived, Some(m), _, _) => write!(f, "{} {}", m.course, m.name)?,
            (_, Some(m), _, _) if &m.course_type == "ap" => write!(f, "{}", m.name)?,
            (_, Some(m), None, Some(ap)) if ap != "" => write!(f, "{} {}", m.course, m.name)?,
            (_, _, Some(c), _) => write!(f, "{}", c)?,
            (_, _, _, _) => write!(f, "?????")?,
        };

        if let Some(inst) = &self.institution {
            write!(f, " [{}]", inst)?;
        }

        writeln!(f)
    }
}

impl crate::to_cell::ToCell for CourseRule {
    fn get_record(
        &self,
        student: &Student,
        _options: &crate::to_cell::CsvOptions,
        is_waived: bool,
    ) -> Vec<(String, String)> {
        let course = if let Some(claim) = self.claims.get(0) {
            student.get_class_by_clbid(&claim.clbid)
        } else {
            None
        };

        let is_waived = is_waived || self.status.is_waived();

        let header = self.course.clone().unwrap_or_else(|| {
            self.ap
                .clone()
                .unwrap_or_else(|| self.crsid.clone().unwrap())
        });
        let body = if let Some(course) = course {
            // if there's a course, show it, even if it was "waived" (ie, it was inserted)
            course.semi_verbose()
        } else if is_waived {
            String::from("<waived>")
        } else if self.status == RuleStatus::Empty {
            String::from(" ")
        } else {
            format!("{:?}", self.status)
        };

        vec![(header, body)]
    }

    fn get_requirements(&self) -> Vec<String> {
        vec![]
    }
}
