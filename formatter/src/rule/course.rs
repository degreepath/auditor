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
    pub course: String,
    pub ap: Option<String>,
    pub institution: Option<String>,
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
        let course = if let Some(claim) = self.claims.get(0) {
            student.get_class_by_clbid(&claim.clbid)
        } else {
            None
        };

        let status = course.map_or("", |c| c.calculate_symbol(&self.status));

        write!(f, "{} ", status)?;

        if self.status == RuleStatus::Waived && course.is_some() {
            let c = course.unwrap();
            write!(f, "{} {}", c.course, c.name)?;
        } else if self.status != RuleStatus::Waived
            && course.is_some()
            && course.clone().unwrap().course_type == "ap"
        {
            write!(f, "{}", course.clone().unwrap().name)?;
        } else if self.course == "" && self.ap.is_some() && self.ap.clone().unwrap() != "" {
            write!(f, "{}", self.ap.clone().unwrap())?;
        } else {
            write!(f, "{}", self.course)?;
        }

        if let Some(inst) = &self.institution {
            write!(f, " [{}]", inst)?;
        }

        writeln!(f)
    }
}

impl crate::to_csv::ToCsv for CourseRule {
    fn get_record(
        &self,
        student: &Student,
        _options: &crate::to_csv::CsvOptions,
    ) -> Vec<(String, String)> {
        let course = if let Some(claim) = self.claims.get(0) {
            student.get_class_by_clbid(&claim.clbid)
        } else {
            None
        };

        if let Some(course) = course {
            vec![(self.course.clone(), course.course_with_term())]
        } else {
            vec![(self.course.clone(), "".into())]
        }
    }
}
