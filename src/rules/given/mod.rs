pub mod all_courses;
pub mod areas_of_study;
pub mod named_variable;
pub mod these_courses;
pub mod these_requirements;

pub mod block;
pub mod common;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum GivenRule {
    AllCourses(all_courses::Rule),
    TheseCourses(these_courses::Rule),
    TheseRequirements(these_requirements::Rule),
    AreasOfStudy(areas_of_study::Rule),
    NamedVariable(named_variable::Rule),
}
