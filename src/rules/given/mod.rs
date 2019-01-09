pub mod action;
pub mod filter;
pub mod limit;

use crate::rules::{course, requirement};

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    #[serde(flatten)]
    pub given: Given,
    #[serde(default, rename = "where")]
    pub filter: Vec<filter::Clause>,
    #[serde(default)]
    pub limit: Vec<limit::Limiter>,
    pub what: What,
    #[serde(rename = "do")]
    pub action: action::Action,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(tag = "given")]
pub enum Given {
    #[serde(rename = "courses")]
    AllCourses,
    #[serde(rename = "these courses")]
    TheseCourses { courses: Vec<course::CourseRule> },
    #[serde(rename = "these requirements")]
    TheseRequirements {
        requirements: Vec<requirement::RequirementRule>,
    },
    #[serde(rename = "areas of study")]
    AreasOfStudy,
    #[serde(rename = "save")]
    NamedVariable { save: action::NamedVariable },
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum What {
    #[serde(rename = "courses")]
    Courses,
    #[serde(rename = "distinct courses")]
    DistinctCourses,
    #[serde(rename = "credits")]
    Credits,
    #[serde(rename = "terms")]
    Terms,
    #[serde(rename = "grades")]
    Grades,
    #[serde(rename = "areas of study")]
    AreasOfStudy,
}
