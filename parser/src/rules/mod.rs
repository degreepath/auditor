pub mod action_only;
pub mod both;
pub mod count_of;
pub mod course;
pub mod either;
pub mod given;
pub mod req_ref;
pub mod traits;

use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Rule {
	Course(#[serde(deserialize_with = "util::string_or_struct")] course::Rule),
	Requirement(req_ref::Rule),
	CountOf(count_of::Rule),
	Both(both::Rule),
	Either(either::Rule),
	Given(given::Rule),
	Do(action_only::Rule),
}

impl crate::rules::traits::PrettyPrint for Rule {
	fn print(&self) -> Result<String, std::fmt::Error> {
		match &self {
			Rule::Course(v) => Ok(format!("take {}", v.print()?)),
			Rule::Requirement(v) => Ok(format!("complete the {} requirement", v.print()?)),
			Rule::CountOf(v) => v.print(),
			Rule::Both(v) => v.print(),
			Rule::Either(v) => v.print(),
			Rule::Given(v) => v.print(),
			Rule::Do(v) => v.print(),
		}
	}
}

impl crate::rules::traits::RuleTools for Rule {
	fn has_save_rule(&self) -> bool {
		match &self {
			Rule::Course(v) => v.has_save_rule(),
			Rule::Requirement(v) => v.has_save_rule(),
			Rule::CountOf(v) => v.has_save_rule(),
			Rule::Both(v) => v.has_save_rule(),
			Rule::Either(v) => v.has_save_rule(),
			Rule::Given(v) => v.has_save_rule(),
			Rule::Do(v) => v.has_save_rule(),
		}
	}
}

impl Rule {
	fn print_inner(&self) -> Result<String, std::fmt::Error> {
		use crate::rules::traits::PrettyPrint;

		match &self {
			Rule::Course(v) => v.print(),
			Rule::Requirement(v) => v.print(),
			Rule::CountOf(v) => v.print(),
			Rule::Both(v) => v.print(),
			Rule::Either(v) => v.print(),
			Rule::Given(v) => v.print(),
			Rule::Do(v) => v.print(),
		}
	}
}

#[cfg(test)]
mod tests {
	use super::*;
	use std::collections::BTreeMap;

	#[test]
	fn deserialize_simple_course_in_array() {
		let data = "---
- STAT 214";

		let expected_struct = vec![Rule::Course(course::Rule {
			course: "STAT 214".to_string(),
			..Default::default()
		})];

		let deserialized: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
		assert_eq!(deserialized, expected_struct);
	}

	#[test]
	fn serialize() {
		let course_a = course::Rule {
			course: "ASIAN 101".to_string(),
			..Default::default()
		};
		let course_b = course::Rule {
			course: "ASIAN 101".to_string(),
			term: Some("2014-1".to_string()),
			..Default::default()
		};
		let data = vec![
			Rule::Course(course_a.clone()),
			Rule::Course(course_b.clone()),
			Rule::Requirement(req_ref::Rule {
				requirement: "Name".to_string(),
				optional: true,
			}),
			Rule::CountOf(count_of::Rule {
				count: count_of::Counter::Number(1),
				of: vec![Rule::Course(course_a.clone())],
				surplus: None,
			}),
			Rule::Both(both::Rule {
				both: (
					Box::new(Rule::Course(course_a.clone())),
					Box::new(Rule::Course(course_b.clone())),
				),
				surplus: None,
			}),
			Rule::Either(either::Rule {
				either: (
					Box::new(Rule::Course(course_a.clone())),
					Box::new(Rule::Course(course_b.clone())),
				),
				surplus: None,
			}),
			Rule::Given(given::Rule {
				given: given::Given::AllCourses,
				what: given::What::Courses,
				filter: Some(BTreeMap::new()),
				limit: Some(vec![]),
				action: "count < 2".parse().unwrap(),
			}),
			Rule::Do(action_only::Rule {
				action: "$a < $b".parse().unwrap(),
			}),
		];

		let expected = r#"---
- course: ASIAN 101
- course: ASIAN 101
  term: 2014-1
  section: ~
  year: ~
  semester: ~
  lab: ~
  international: ~
- requirement: Name
  optional: true
- count: 1
  of:
    - course: ASIAN 101
  surplus: ~
- both:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
  surplus: ~
- either:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
  surplus: ~
- given: courses
  limit: []
  where: {}
  what: courses
  do:
    lhs:
      Command: Count
    op: LessThan
    rhs:
      Integer: 2
- do:
    lhs:
      String: $a
    op: LessThan
    rhs:
      String: $b"#;

		let actual = serde_yaml::to_string(&data).unwrap();
		assert_eq!(actual, expected, "actual: {}\n\nexpected: {}", actual, expected);
	}

	#[test]
	fn deserialize() {
		let course_a = course::Rule {
			course: "ASIAN 101".to_string(),
			..Default::default()
		};
		let course_b = course::Rule {
			course: "ASIAN 101".to_string(),
			term: Some("2014-1".to_string()),
			..Default::default()
		};
		let expected = vec![
			Rule::Course(course_a.clone()),
			Rule::Course(course_b.clone()),
			Rule::Requirement(req_ref::Rule {
				requirement: "Name".to_string(),
				optional: true,
			}),
			Rule::CountOf(count_of::Rule {
				count: count_of::Counter::Number(1),
				of: vec![Rule::Course(course_a.clone())],
				surplus: None,
			}),
			Rule::Both(both::Rule {
				both: (
					Box::new(Rule::Course(course_a.clone())),
					Box::new(Rule::Course(course_b.clone())),
				),
				surplus: None,
			}),
			Rule::Either(either::Rule {
				either: (
					Box::new(Rule::Course(course_a.clone())),
					Box::new(Rule::Course(course_b.clone())),
				),
				surplus: None,
			}),
			Rule::Given(given::Rule {
				given: given::Given::AllCourses,
				what: given::What::Courses,
				filter: Some(BTreeMap::new()),
				limit: Some(vec![]),
				action: "count < 2".parse().unwrap(),
			}),
			Rule::Do(action_only::Rule {
				action: "$a < $b".parse().unwrap(),
			}),
		];

		let data = r#"---
- course: ASIAN 101
- course: ASIAN 101
  term: 2014-1
  section: ~
  year: ~
  semester: ~
  lab: ~
  international: ~
- requirement: Name
  optional: true
- count: 1
  of:
    - course: ASIAN 101
  surplus: ~
- both:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
  surplus: ~
- either:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
  surplus: ~
- given: courses
  what: courses
  where: {}
  limit: []
  do: count < 2
- do: $a < $b"#;

		let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);

		let data = r#"---
- course: ASIAN 101
- course: ASIAN 101
  term: 2014-1
  section: ~
  year: ~
  semester: ~
  lab: ~
  international: ~
- requirement: Name
  optional: true
- count: 1
  of:
    - course: ASIAN 101
  surplus: ~
- both:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
  surplus: ~
- either:
    - course: ASIAN 101
    - course: ASIAN 101
      term: 2014-1
      section: ~
      year: ~
      semester: ~
      lab: ~
      international: ~
  surplus: ~
- given: courses
  what: courses
  where: {}
  limit: []
  do: count < 2
- do: $a < $b"#;

		let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_shorthands() {
		let data = r#"---
- ASIAN 101
- course: ASIAN 101
- {course: ASIAN 102, term: 2014-1}
- requirement: Name 1
- {requirement: Name 2, optional: true}
- count: 1
  of:
    - ASIAN 101
- both:
    - ASIAN 101
    - {course: ASIAN 102, term: 2014-1}
- either:
    - ASIAN 101
    - {course: ASIAN 102, term: 2014-1}
- given: courses
  what: courses
  do: count < 2
- do: $a < $b"#;

		let course_a = course::Rule {
			course: "ASIAN 101".to_string(),
			..Default::default()
		};
		let course_b = course::Rule {
			course: "ASIAN 102".to_string(),
			term: Some("2014-1".to_string()),
			..Default::default()
		};
		let expected = vec![
			Rule::Course(course_a.clone()),
			Rule::Course(course_a.clone()),
			Rule::Course(course_b.clone()),
			Rule::Requirement(req_ref::Rule {
				requirement: "Name 1".to_string(),
				optional: false,
			}),
			Rule::Requirement(req_ref::Rule {
				requirement: "Name 2".to_string(),
				optional: true,
			}),
			Rule::CountOf(count_of::Rule {
				count: count_of::Counter::Number(1),
				of: vec![Rule::Course(course_a.clone())],
				surplus: None,
			}),
			Rule::Both(both::Rule {
				both: (
					Box::new(Rule::Course(course_a.clone())),
					Box::new(Rule::Course(course_b.clone())),
				),
				surplus: None,
			}),
			Rule::Either(either::Rule {
				either: (
					Box::new(Rule::Course(course_a.clone())),
					Box::new(Rule::Course(course_b.clone())),
				),
				surplus: None,
			}),
			Rule::Given(given::Rule {
				given: given::Given::AllCourses,
				what: given::What::Courses,
				filter: None,
				limit: None,
				action: "count < 2".parse().unwrap(),
			}),
			Rule::Do(action_only::Rule {
				action: "$a < $b".parse().unwrap(),
			}),
		];

		let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}

	#[test]
	fn pretty_print() {
		use crate::rules::traits::PrettyPrint;

		let data = r#"---
- ASIAN 101
- course: ASIAN 101
- {course: ASIAN 102, term: 2014-1}
- requirement: Name 1
- {requirement: Name 2, optional: true}
- {count: 1, of: [ASIAN 101]}
- {both: [ASIAN 101, {course: ASIAN 102, term: 2014-1}]}
- {either: [ASIAN 101, {course: ASIAN 102, term: 2014-1}]}
- {given: courses, what: courses, do: count < 2}
- do: >
    "X" < "Y"
"#;

		let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
		let actual: Vec<String> = actual
			.into_iter()
			.filter_map(|r| match r.print() {
				Ok(p) => Some(p),
				Err(_) => None,
			})
			.collect();

		let expected = vec![
			"take ASIAN 101",
			"take ASIAN 101",
			"take ASIAN 102 (2014-1)",
			"complete the “Name 1” requirement",
			"complete the “Name 2” (optional) requirement",
			"take ASIAN 101",
			"take both ASIAN 101 and ASIAN 102 (2014-1)",
			"take either ASIAN 101 or ASIAN 102 (2014-1)",
			"take fewer than two courses",
			"ensure that the computed result of the subset “X” is less than the computed result of the subset “Y”",
		];

		assert_eq!(actual, expected, "left: {:#?}\n\nright: {:#?}", actual, expected);
	}

	#[test]
	fn dance_seminar() {
		let expected = Rule::Given(given::Rule {
			given: given::Given::NamedVariable {
				save: "Senior Dance Seminars".to_string(),
			},
			what: given::What::Courses,
			filter: None,
			limit: None,
			action: "count >= 1".parse().unwrap(),
		});

		let data = r#"---
given: save
save: "Senior Dance Seminars"
what: courses
do: count >= 1
"#;

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);

		let data = r#"---
given: save
save: "Senior Dance Seminars"
what: courses
do:
  lhs:
    Command: Count
  op: GreaterThanEqualTo
  rhs:
    Integer: 1
"#;

		let actual: Rule = serde_yaml::from_str(&data).unwrap();
		assert_eq!(actual, expected);
	}
}
