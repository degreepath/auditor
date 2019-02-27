use super::*;
use crate::student::Semester;
use crate::traits::print::Print;
use std::collections::BTreeMap;
use insta::{assert_debug_snapshot_matches, assert_yaml_snapshot_matches};

#[test]
fn deserialize_simple_course_in_array() {
	let data = "---
- STAT 214";

	let deserialized: Vec<Rule> = serde_yaml::from_str(&data).unwrap();

	assert_debug_snapshot_matches!(deserialized, @r###"[
    Course(
        Rule {
            course: "STAT 214",
            grade: None,
            section: None,
            year: None,
            semester: None,
            lab: None,
            can_match_used: None
        }
    )
]"###);
}

#[test]
fn serialize() {
	let course_a = course::Rule {
		course: "ASIAN 101".to_string(),
		..Default::default()
	};
	let course_b = course::Rule {
		course: "ASIAN 101".to_string(),
		semester: Some(Semester::Fall),
		year: Some(2014),
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
		}),
		Rule::Both(both::Rule {
			both: (
				Box::new(Rule::Course(course_a.clone())),
				Box::new(Rule::Course(course_b.clone())),
			),
		}),
		Rule::Either(either::Rule {
			either: (
				Box::new(Rule::Course(course_a.clone())),
				Box::new(Rule::Course(course_b.clone())),
			),
		}),
		Rule::Given(given::Rule {
			given: given::Given::AllCourses {
				what: given::GivenCoursesWhatOptions::Courses,
			},
			filter: Some(BTreeMap::new()),
			limit: Some(vec![]),
			action: "count < 2".parse().unwrap(),
		}),
		Rule::Do(action_only::Rule {
			action: crate::action::LhsValueAction {
				lhs: crate::action::Value::String("a".to_string()),
				op: Some(crate::action::Operator::LessThan),
				rhs: Some(crate::action::Value::String("b".to_string())),
			},
		}),
	];

	assert_yaml_snapshot_matches!("serialize_mix_1", data);
}

#[test]
fn deserialize() {
	let data = r#"---
- course: ASIAN 101
- course: ASIAN 101
  section: ~
  year: 2014
  semester: Fall
  lab: ~
- requirement: Name
  optional: true
- count: 1
  of:
    - course: ASIAN 101
- both:
    - course: ASIAN 101
    - course: ASIAN 101
      section: ~
      year: 2014
      semester: Fall
      lab: ~
- either:
    - course: ASIAN 101
    - course: ASIAN 101
      section: ~
      year: 2014
      semester: Fall
      lab: ~
- given: courses
  what: courses
  where: {}
  limit: []
  do: count < 2
- do: {lhs: a, op: <, rhs: b}"#;

	let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
	assert_debug_snapshot_matches!("deserialize_mix", actual);
}

#[test]
fn deserialize_shorthands() {
	let data = r#"---
- ASIAN 101
- course: ASIAN 101
- {course: ASIAN 102, year: 2014, semester: Fall}
- requirement: Name 1
- {requirement: Name 2, optional: true}
- count: 1
  of:
    - ASIAN 101
- both:
    - ASIAN 101
    - {course: ASIAN 102, year: 2014, semester: Fall}
- either:
    - ASIAN 101
    - {course: ASIAN 102, year: 2014, semester: Fall}
- given: courses
  what: courses
  do: count < 2
- do: {lhs: a, op: <, rhs: b}"#;

	let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
	assert_debug_snapshot_matches!("deserialize_shorthands", actual);
}

#[test]
fn pretty_print() {
	let data = r#"---
- ASIAN 101
- course: ASIAN 101
- {course: ASIAN 102, year: 2014, semester: Fall}
- requirement: Name 1
- {requirement: Name 2, optional: true}
- {count: 1, of: [ASIAN 101]}
- {both: [ASIAN 101, {course: ASIAN 102, year: 2014, semester: Fall}]}
- {either: [ASIAN 101, {course: ASIAN 102, year: 2014, semester: Fall}]}
- {given: courses, what: courses, do: count < 2}
- {do: {lhs: X, op: <, rhs: Y}}
"#;

	let actual: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
	let actual: Vec<String> = actual
		.into_iter()
		.filter_map(|r| match r.print() {
			Ok(p) => Some(p),
			Err(_) => None,
		})
		.collect();

	assert_debug_snapshot_matches!("pretty_print_mix", actual);
}

#[test]
fn dance_seminar() {
	let expected = Rule::Given(given::Rule {
		given: given::Given::NamedVariable {
			save: "Senior Dance Seminars".to_string(),
			what: given::GivenCoursesWhatOptions::Courses,
		},
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
  lhs: Count
  op: GreaterThanEqualTo
  rhs:
    Integer: 1
"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}
