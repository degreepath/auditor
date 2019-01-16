use crate::rules::Rule;
use crate::save::SaveBlock;
use crate::util;
use std::collections::HashMap;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Requirement {
	#[serde(default)]
	pub message: Option<String>,
	#[serde(default = "util::serde_false")]
	pub department_audited: bool,
	#[serde(default)]
	pub result: Option<Rule>,
	#[serde(default = "util::serde_false")]
	pub contract: bool,
	#[serde(default)]
	pub save: Vec<SaveBlock>,
	#[serde(default)]
	pub requirements: HashMap<String, Requirement>,
}

#[cfg(test)]
mod tests {
	use super::*;
	use crate::rules;
	use crate::rules::{given, requirement};

	#[test]
	fn serialize() {
		let data = Requirement {
			message: None,
			department_audited: false,
			result: Some(Rule::Requirement(requirement::Rule {
				requirement: String::from("name"),
				optional: false,
			})),
			contract: false,
			save: vec![],
			requirements: HashMap::new(),
		};

		let expected = "---
message: ~
department_audited: false
result:
  requirement: name
  optional: false
contract: false
save: []
requirements: {}";

		let actual = serde_yaml::to_string(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize() {
		let data = "---
message: ~
department_audited: false
result:
  requirement: name
  optional: false
contract: false
save: []
requirements: {}";

		let expected = Requirement {
			message: None,
			department_audited: false,
			result: Some(Rule::Requirement(requirement::Rule {
				requirement: String::from("name"),
				optional: false,
			})),
			contract: false,
			save: vec![],
			requirements: HashMap::new(),
		};

		let actual: Requirement = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_with_defaults() {
		let data = "---
message: ~
result: {requirement: name, optional: false}";

		let expected = Requirement {
			message: None,
			department_audited: false,
			result: Some(Rule::Requirement(requirement::Rule {
				requirement: String::from("name"),
				optional: false,
			})),
			contract: false,
			save: vec![],
			requirements: HashMap::new(),
		};

		let actual: Requirement = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_message_only() {
		let data = "---
message: a message";

		let expected = Requirement {
			message: Some("a message".to_string()),
			department_audited: false,
			result: None,
			contract: false,
			save: vec![],
			requirements: HashMap::new(),
		};

		let actual: Requirement = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_ba_interim() {
		let data = "---
save:
  - given: courses
    where: {semester: Interim}
    what: courses
    name: Interim Courses
result:
  both:
    - {given: save, save: Interim Courses, what: credits, do: sum >= 3}
    - {given: save, save: Interim Courses, what: courses, do: count >= 3}";

		let expected_filter: given::filter::Clause = hashmap! {
			"semester".into() => "Interim".parse::<given::filter::WrappedValue>().unwrap(),
		};

		let expected = Requirement {
			message: None,
			department_audited: false,
			result: Some(Rule::Both(rules::both::Rule {
				both: (
					Box::new(Rule::Given(given::Rule {
						given: given::Given::NamedVariable {
							save: "Interim Courses".to_string(),
						},
						limit: None,
						filter: None,
						what: given::What::Credits,
						action: "sum >= 3".parse().unwrap(),
					})),
					Box::new(Rule::Given(given::Rule {
						given: given::Given::NamedVariable {
							save: "Interim Courses".to_string(),
						},
						limit: None,
						filter: None,
						what: given::What::Courses,
						action: "count >= 3".parse().unwrap(),
					})),
				),
			})),
			contract: false,
			save: vec![SaveBlock {
				name: "Interim Courses".to_string(),
				given: given::Given::AllCourses,
				limit: None,
				filter: Some(expected_filter),
				what: Some(given::What::Courses),
				action: None,
			}],
			requirements: HashMap::new(),
		};

		let actual: Requirement = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}
}
