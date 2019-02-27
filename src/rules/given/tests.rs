use super::Rule;
use super::{CourseRule, Given, GivenAreasWhatOptions, GivenCoursesWhatOptions, RepeatMode};
use crate::filter;
use crate::rules::{course, req_ref};
use crate::traits::print::Print;
use crate::value;
use insta::{assert_snapshot_matches, assert_debug_snapshot_matches};
use maplit::btreemap;

#[test]
fn serialize_all_courses() {
	let data = Rule {
		given: Given::AllCourses {
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	assert_debug_snapshot_matches!("ser_all_courses", data);
}

#[test]
fn deserialize_all_courses() {
	let expected = Rule {
		given: Given::AllCourses {
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: courses
what: courses
limit: []
where: {}
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: courses
what: courses
limit: []
where: {}
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn serialize_these_courses() {
	let data = Rule {
		given: Given::TheseCourses {
			courses: vec![
				CourseRule::Value(course::Rule {
					course: "ASIAN 110".to_string(),
					..Default::default()
				}),
				CourseRule::Value(course::Rule {
					course: "ASIAN 110".to_string(),
					..Default::default()
				}),
			],
			repeats: RepeatMode::First,
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	assert_debug_snapshot_matches!("ser_these_courses_1", data);
}

#[test]
fn deserialize_these_courses() {
	let expected = Rule {
		given: Given::TheseCourses {
			courses: vec![
				CourseRule::Value(course::Rule {
					course: "ASIAN 110".to_string(),
					..Default::default()
				}),
				CourseRule::Value(course::Rule {
					course: "ASIAN 110".to_string(),
					..Default::default()
				}),
			],
			repeats: RepeatMode::First,
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: these-courses
courses:
  - ASIAN 110
  - course: ASIAN 110
repeats: first
what: courses
limit: []
where: {}
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: these-courses
courses:
  - ASIAN 110
  - course: ASIAN 110
repeats: first
what: courses
limit: []
where: {}
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn serialize_these_requirements() {
	let data = Rule {
		given: Given::TheseRequirements {
			requirements: vec![
				req_ref::Rule {
					requirement: "A Name 1".to_string(),
					optional: false,
				},
				req_ref::Rule {
					requirement: "A Name 2".to_string(),
					optional: true,
				},
			],
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	assert_debug_snapshot_matches!("ser_these_reqs", data);
}

#[test]
fn deserialize_these_requirements() {
	let expected = Rule {
		given: Given::TheseRequirements {
			requirements: vec![
				req_ref::Rule {
					requirement: "A Name 1".to_string(),
					optional: false,
				},
				req_ref::Rule {
					requirement: "A Name 2".to_string(),
					optional: true,
				},
			],
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: these-requirements
requirements:
  - requirement: A Name 1
  - {requirement: A Name 2, optional: true}
what: courses
limit: []
where: {}
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: these-requirements
requirements:
  - requirement: A Name 1
  - {requirement: A Name 2, optional: true}
what: courses
limit: []
where: {}
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn serialize_areas() {
	let data = Rule {
		given: Given::Areas {
			what: GivenAreasWhatOptions::Areas,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	assert_debug_snapshot_matches!("ser_areas", data);
}

#[test]
fn deserialize_areas() {
	let expected = Rule {
		given: Given::Areas {
			what: GivenAreasWhatOptions::Areas,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: areas
what: areas
limit: []
where: {}
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: areas
what: areas
limit: []
where: {}
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn serialize_save() {
	let data = Rule {
		given: Given::NamedVariable {
			save: String::from("$my_var"),
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	assert_debug_snapshot_matches!("ser_save", data);
}

#[test]
fn deserialize_save() {
	let expected = Rule {
		given: Given::NamedVariable {
			save: String::from("$my_var"),
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: save
save: $my_var
what: courses
limit: []
where: {}
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: save
save: $my_var
what: courses
limit: []
where: {}
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_save_ba_interim() {
	let data = r#"---
given: save
save: $interim_courses
what: courses
do: count >= 3"#;

	let expected = Rule {
		given: Given::NamedVariable {
			save: String::from("$interim_courses"),
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: None,
		filter: None,
		action: "count >= 3".parse().unwrap(),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_gereqs_single() {
	let data = r#"{where: {gereqs: 'FYW'}, given: courses, what: courses, do: count > 1}"#;

	let expected: filter::Clause = btreemap! {
		"gereqs".into() => value::WrappedValue::eq_string("FYW"),
	};
	let expected = Rule {
		given: Given::AllCourses {
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: None,
		filter: Some(expected),
		action: "count > 1".parse().unwrap(),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_gereqs_or() {
	use value::{TaggedValue, WrappedValue};
	let data = r#"{where: {gereqs: 'MCD | MCG'}, given: courses, what: courses, do: count > 1}"#;

	let expected: filter::Clause = btreemap! {
		"gereqs".into() => WrappedValue::Or(vec![
			TaggedValue::eq_string("MCD"),
			TaggedValue::eq_string("MCG"),
		]),
	};
	let expected = Rule {
		given: Given::AllCourses {
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: None,
		filter: Some(expected),
		action: "count > 1".parse().unwrap(),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_level_gte() {
	use value::{SingleValue::Integer, TaggedValue::GreaterThanEqualTo, WrappedValue::Single};
	let data = r#"{where: {level: '>= 200'}, given: courses, what: courses, do: count > 1}"#;

	let expected: filter::Clause = btreemap! {
		"level".into() => Single(GreaterThanEqualTo(Integer(200)))
	};
	let expected = Rule {
		given: Given::AllCourses {
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: None,
		filter: Some(expected),
		action: "count > 1".parse().unwrap(),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_graded_bool() {
	use value::{SingleValue::Bool, TaggedValue::EqualTo, WrappedValue::Single};
	let data = r#"{where: {graded: 'true'}, given: courses, what: courses, do: count > 1}"#;

	let expected: filter::Clause = btreemap! {
		"graded".into() => Single(EqualTo(Bool(true))),
	};
	let expected = Rule {
		given: Given::AllCourses {
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: None,
		filter: Some(expected),
		action: "count > 1".parse().unwrap(),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn pretty_print_inline() {
	let input: Rule = serde_yaml::from_str(&"{given: courses, what: courses, do: count >= 1}").unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take at least one course");
}

#[test]
fn pretty_print_inline_filters() {
	let s = "{given: courses, where: {gereqs: FOL-C}, what: courses, do: count >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take at least one course with the “FOL-C” general education attribute");

	let s = "{given: courses, where: {gereqs: SPM}, what: distinct-courses, do: count >= 2}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take at least two distinct courses with the “SPM” general education attribute");
}

#[test]
fn pretty_print_inline_repeats() {
	let s = "{given: these-courses, repeats: all, courses: [THEAT 233], what: courses, do: count >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take THEAT 233 at least one time");

	let s = "{given: these-courses, repeats: all, courses: [THEAT 233], what: courses, do: count >= 4}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take THEAT 233 at least four times");

	let s = "{given: these-courses, repeats: all, courses: [THEAT 233, THEAT 253], what: courses, do: count >= 4}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take a combination of THEAT 233 and THEAT 253 at least four times");

	let s = "{given: these-courses, repeats: all, courses: [AMST 205, AMST 206, AMST 207, AMST 208, AMST 209, AMST 210], what: courses, do: count >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"take at least one of the following courses:

- AMST 205
- AMST 206
- AMST 207
- AMST 208
- AMST 209
- AMST 210"###);

	let s = "{given: these-courses, repeats: all, courses: [THEAT 233], what: credits, do: sum >= 4}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take THEAT 233 enough times to yield at least four credits");

	let s = "{given: these-courses, repeats: first, courses: [THEAT 233], what: courses, do: count >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take THEAT 233");

	let s = "{given: these-courses, repeats: first, courses: [THEAT 233, THEAT 253], what: courses, do: count >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take either THEAT 233 or THEAT 253");

	let s = "{given: these-courses, repeats: first, courses: [THEAT 233, THEAT 253], what: courses, do: count >= 2}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take both THEAT 233 and THEAT 253");
}

#[test]
fn pretty_print_inline_credits() {
	let s = "{given: courses, where: {gereqs: FOL-C}, what: credits, do: sum >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken with the “FOL-C” general education attribute to obtain at least one credit");

	let s = "{given: courses, where: {semester: Interim}, what: credits, do: sum >= 3}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during Interim semesters to obtain at least three credits");

	let s = "{given: courses, where: {semester: Fall}, what: credits, do: sum >= 10}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during Fall semesters to obtain at least ten credits");

	let s = "{given: courses, where: {semester: Fall | Interim}, what: credits, do: sum >= 10}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during a Fall or Interim semester to obtain at least ten credits");

	let s = "{given: courses, where: {year: '2012'}, what: credits, do: sum >= 3}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during the 2012-13 academic year to obtain at least three credits");

	let s = "{given: courses, where: {institution: St. Olaf College}, what: credits, do: sum >= 17}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken at St. Olaf College to obtain at least 17 credits");
}

#[test]
fn pretty_print_inline_departments() {
	let s = "{given: courses, where: {gereqs: FOL-C}, what: departments, do: count >= 2}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken with the “FOL-C” general education attribute to span at least two departments");

	let s = "{given: courses, where: {semester: Interim}, what: departments, do: count >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during Interim semesters to span at least one department");

	let s = "{given: courses, where: { department: '! MATH' }, what: departments, do: count >= 2}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken outside of the MATH department to span at least two departments");
}

#[test]
fn pretty_print_inline_grades() {
	let s = "{given: courses, where: { gereqs: FOL-C }, what: grades, do: average >= 2.0}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"maintain an average GPA at or above 2.00 from courses taken with the “FOL-C” general education attribute");

	let s = "{given: courses, where: { semester: Interim }, what: grades, do: average >= 3.0}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"maintain an average GPA at or above 3.00 from courses taken during Interim semesters");
}

#[test]
fn pretty_print_inline_terms() {
	let s = "{given: courses, where: { gereqs: FOL-C }, what: terms, do: count >= 2}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have taken enough courses with the “FOL-C” general education attribute to span at least two terms");

	let s = "{given: courses, where: { semester: Interim }, what: terms, do: count >= 3}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have taken enough courses during Interim semesters to span at least three terms");
}

#[test]
fn pretty_print_inline_given_requirements_what_courses() {
	let s = "{given: these-requirements, requirements: [{requirement: Core}, {requirement: Modern}], what: credits, do: sum >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. there must be at least one credit
"###);

	let s = "{given: these-requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { gereqs: FOL-C }, what: credits, do: sum >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken with the “FOL-C” general education attribute,
3. there must be at least one credit
"###);

	let s = "{given: these-requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { semester: Interim }, what: credits, do: sum >= 3}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during Interim semesters,
3. there must be at least three credits
"###);

	let s = "{given: these-requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { semester: Fall }, what: credits, do: sum >= 10}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during Fall semesters,
3. there must be at least ten credits
"###);

	let s = "{given: these-requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { year: '2012' }, what: credits, do: sum >= 1}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during the 2012-13 academic year,
3. there must be at least one credit
");

	let s = "{given: these-requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { institution: St. Olaf College }, what: credits, do: sum >= 17}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken at St. Olaf College,
3. there must be at least 17 credits
"###);
}
