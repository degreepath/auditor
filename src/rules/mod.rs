pub mod both;
pub mod count_of;
pub mod course;
pub mod either;
pub mod given;
pub mod requirement;

use crate::util::string_or_struct;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Rule {
    Course(#[serde(deserialize_with = "string_or_struct")] course::CourseRule),
    Requirement(requirement::RequirementRule),
    CountOf(count_of::CountOfRule),
    Both(both::BothRule),
    Either(either::EitherRule),
    Given(given::GivenRule),
}
