pub mod action;
pub mod filter;
pub mod limit;

use crate::rules::{course, requirement};

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    #[serde(flatten)]
    pub given: Given,
    #[serde(default)]
    pub limit: Vec<limit::Limiter>,
    #[serde(default, rename = "where")]
    pub filter: filter::Clause,
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

#[cfg(test)]
mod tests {
	use super::*;
	use std::collections::HashMap;

	#[test]
	fn serialize_all_courses() {
		let data = Rule {
			given: Given::AllCourses,
			limit: vec![],
			filter: HashMap::new(),
			what: What::Courses,
			action: "count > 2".parse().unwrap(),
		};

		let expected = r#"---
given: courses
limit: []
where: {}
what: courses
do:
  lhs:
    Command: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

		let actual = serde_yaml::to_string(&data).unwrap();

		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_all_courses() {}

	#[test]
	fn serialize_these_courses() {}

	#[test]
	fn deserialize_these_courses() {}

	#[test]
	fn serialize_these_requirements() {}

	#[test]
	fn deserialize_these_requirements() {}

	#[test]
	fn serialize_areas() {}

	#[test]
	fn deserialize_areas() {}

	#[test]
	fn serialize_save() {}

	#[test]
	fn deserialize_save() {}
}
