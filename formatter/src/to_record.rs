use crate::student;

#[derive(Debug, Clone)]
pub struct Record {
    pub title: String,
    pub subtitle: Option<String>,
    pub status: crate::rule::RuleStatus,
    pub content: Vec<Cell>,
}

impl Record {
    pub(crate) fn with_title(&self, new_title: &str) -> Record {
        Record {
            title: new_title.to_string(),
            ..self.clone()
        }
    }

    pub fn new(title: &str, content: &str) -> Record {
        Record {
            title: String::from(title),
            subtitle: None,
            status: RecordStatus::Empty,
            content: vec![Cell::Text(String::from(content))],
        }
    }

    pub fn is_ok(&self) -> bool {
        self.status.is_passing()
    }

    pub fn status_class(&self) -> &str {
        self.status.as_classname()
    }
}

pub type RecordStatus = crate::rule::RuleStatus;

#[derive(Debug, Clone)]
pub enum Cell {
    Text(String),
    SingleCourse(student::Course),
    DoneCourses(Vec<student::Course>),
    InProgressCourses(Vec<student::Course>),
}

impl Cell {
    pub fn render(&self) -> String {
        match self {
            Cell::Text(text) => text.clone(),
            Cell::SingleCourse(c) => c.semi_verbose(),
            Cell::DoneCourses(courses) => courses
                .iter()
                .map(|c| c.semi_verbose())
                .collect::<Vec<_>>()
                .join("<br>"),
            Cell::InProgressCourses(courses) => courses
                .iter()
                .map(|c| c.semi_verbose())
                .collect::<Vec<_>>()
                .join("<br>"),
        }
    }
}

pub trait ToRecord {
    fn get_row(
        &self,
        student: &student::Student,
        options: &RecordOptions,
        is_waived: bool,
    ) -> Vec<Record>;

    fn get_requirements(&self) -> Vec<String>;

    fn emphasis_requirement_names(&self) -> Vec<String> {
        use std::collections::BTreeSet;
        self.get_requirements()
            .iter()
            .filter(|e| e.starts_with("Emphasis: "))
            .map(|name| String::from(name.split(" → ").take(1).last().unwrap()))
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect()
    }
}

pub struct RecordOptions {}
