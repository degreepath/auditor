use super::Rule;
use super::{CourseRule, Given, RepeatMode, What};
use crate::filter;
use crate::rules::{course, req_ref};
use crate::traits::print::Print;
use crate::value;
use maplit::btreemap;

#[test]
fn serialize_all_courses() {
	let data = Rule {
		given: Given::AllCourses,
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::Courses,
		action: "count > 2".parse().unwrap(),
	};

	let expected = r#"---
given: courses
limit: []
where: {}
what: courses
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual = serde_yaml::to_string(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_all_courses() {
	let expected = Rule {
		given: Given::AllCourses,
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::Courses,
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: courses
limit: []
where: {}
what: courses
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: courses
limit: []
where: {}
what: courses
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
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::Courses,
		action: "count > 2".parse().unwrap(),
	};

	let expected = r#"---
given: these courses
courses:
  - course: ASIAN 110
  - course: ASIAN 110
repeats: first
limit: []
where: {}
what: courses
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual = serde_yaml::to_string(&data).unwrap();

	assert_eq!(actual, expected);
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
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::Courses,
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: these courses
courses:
  - ASIAN 110
  - course: ASIAN 110
repeats: first
limit: []
where: {}
what: courses
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: these courses
courses:
  - ASIAN 110
  - course: ASIAN 110
repeats: first
limit: []
where: {}
what: courses
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
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::Courses,
		action: "count > 2".parse().unwrap(),
	};

	let expected = r#"---
given: these requirements
requirements:
  - requirement: A Name 1
    optional: false
  - requirement: A Name 2
    optional: true
limit: []
where: {}
what: courses
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual = serde_yaml::to_string(&data).unwrap();

	assert_eq!(actual, expected);
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
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::Courses,
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: these requirements
requirements:
  - requirement: A Name 1
  - {requirement: A Name 2, optional: true}
limit: []
where: {}
what: courses
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: these requirements
requirements:
  - requirement: A Name 1
  - {requirement: A Name 2, optional: true}
limit: []
where: {}
what: courses
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
		given: Given::AreasOfStudy,
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::AreasOfStudy,
		action: "count > 2".parse().unwrap(),
	};

	let expected = r#"---
given: areas of study
limit: []
where: {}
what: areas of study
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual = serde_yaml::to_string(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_areas() {
	let expected = Rule {
		given: Given::AreasOfStudy,
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::AreasOfStudy,
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: areas of study
limit: []
where: {}
what: areas of study
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: areas of study
limit: []
where: {}
what: areas of study
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
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::Courses,
		action: "count > 2".parse().unwrap(),
	};

	let expected = r#"---
given: save
save: $my_var
limit: []
where: {}
what: courses
do:
  lhs: Count
  op: GreaterThan
  rhs:
    Integer: 2"#;

	let actual = serde_yaml::to_string(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_save() {
	let expected = Rule {
		given: Given::NamedVariable {
			save: String::from("$my_var"),
		},
		limit: Some(vec![]),
		filter: Some(filter::Clause::new()),
		what: What::Courses,
		action: "count > 2".parse().unwrap(),
	};

	let data = r#"---
given: save
save: $my_var
limit: []
where: {}
what: courses
do: count > 2"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
given: save
save: $my_var
limit: []
where: {}
what: courses
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
		},
		limit: None,
		filter: None,
		what: What::Courses,
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
		given: Given::AllCourses,
		limit: None,
		filter: Some(expected),
		what: What::Courses,
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
		given: Given::AllCourses,
		limit: None,
		filter: Some(expected),
		what: What::Courses,
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
		given: Given::AllCourses,
		limit: None,
		filter: Some(expected),
		what: What::Courses,
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
		given: Given::AllCourses,
		limit: None,
		filter: Some(expected),
		what: What::Courses,
		action: "count > 1".parse().unwrap(),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn pretty_print_inline() {
	let input: Rule = serde_yaml::from_str(&"{given: courses, what: courses, do: count >= 1}").unwrap();
	let expected = "have at least one course";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_inline_filters() {
	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {gereqs: FOL-C}, what: courses, do: count >= 1}").unwrap();
	let expected = "have at least one course taken with the “FOL-C” general education attribute";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {gereqs: SPM}, what: distinct courses, do: count >= 2}")
			.unwrap();
	let expected = "have at least two distinct courses taken with the “SPM” general education attribute";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_inline_repeats() {
	let input: Rule = serde_yaml::from_str(
		&"{given: these courses, repeats: all, courses: [THEAT 233], what: courses, do: count >= 1}",
	)
	.unwrap();
	let expected = "take THEAT 233 at least one time";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{given: these courses, repeats: all, courses: [THEAT 233], what: courses, do: count >= 4}",
	)
	.unwrap();
	let expected = "take THEAT 233 at least four times";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{given: these courses, repeats: all, courses: [THEAT 233, THEAT 253], what: courses, do: count >= 4}",
	)
	.unwrap();
	let expected = "take a combination of THEAT 233 and THEAT 253 at least four times";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{given: these courses, repeats: all, courses: [AMST 205, AMST 206, AMST 207, AMST 208, AMST 209, AMST 210], what: courses, do: count >= 1}", ) .unwrap();
	let expected = "take at least one of the following courses:

- AMST 205
- AMST 206
- AMST 207
- AMST 208
- AMST 209
- AMST 210";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{given: these courses, repeats: all, courses: [THEAT 233], what: credits, do: sum >= 4}",
	)
	.unwrap();
	let expected = "take THEAT 233 enough times to yield at least four credits";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{given: these courses, repeats: first, courses: [THEAT 233], what: courses, do: count >= 1}",
	)
	.unwrap();
	let expected = "take THEAT 233";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{given: these courses, repeats: first, courses: [THEAT 233, THEAT 253], what: courses, do: count >= 1}",
	)
	.unwrap();
	let expected = "take either THEAT 233 or THEAT 253";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{given: these courses, repeats: first, courses: [THEAT 233, THEAT 253], what: courses, do: count >= 2}",
	)
	.unwrap();
	let expected = "take both THEAT 233 and THEAT 253";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_inline_credits() {
	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {gereqs: FOL-C}, what: credits, do: sum >= 1}").unwrap();
	let expected =
		"have enough courses taken with the “FOL-C” general education attribute to obtain at least one credit";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {semester: Interim}, what: credits, do: sum >= 3}").unwrap();
	let expected = "have enough courses taken during Interim semesters to obtain at least three credits";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {semester: Fall}, what: credits, do: sum >= 10}").unwrap();
	let expected = "have enough courses taken during Fall semesters to obtain at least ten credits";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {semester: Fall | Interim}, what: credits, do: sum >= 10}")
			.unwrap();
	let expected = "have enough courses taken during a Fall or Interim semester to obtain at least ten credits";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {year: '2012'}, what: credits, do: sum >= 3}").unwrap();
	let expected = "have enough courses taken during the 2012-13 academic year to obtain at least three credits";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {institution: St. Olaf College}, what: credits, do: sum >= 17}")
			.unwrap();
	let expected = "have enough courses taken at St. Olaf College to obtain at least 17 credits";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_inline_departments() {
	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {gereqs: FOL-C}, what: departments, do: count >= 2}").unwrap();
	let expected =
		"have enough courses taken with the “FOL-C” general education attribute to span at least two departments";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: {semester: Interim}, what: departments, do: count >= 1}")
			.unwrap();
	let expected = "have enough courses taken during Interim semesters to span at least one department";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: { department: '! MATH' }, what: departments, do: count >= 2}")
			.unwrap();
	let expected = "have enough courses taken outside of the MATH department to span at least two departments";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_inline_grades() {
	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: { gereqs: FOL-C }, what: grades, do: average >= 2.0}").unwrap();
	let expected =
		"maintain an average GPA at or above 2.00 from courses taken with the “FOL-C” general education attribute";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: { semester: Interim }, what: grades, do: average >= 3.0}")
			.unwrap();
	let expected = "maintain an average GPA at or above 3.00 from courses taken during Interim semesters";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_inline_terms() {
	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: { gereqs: FOL-C }, what: terms, do: count >= 2}").unwrap();
	let expected =
		"have enough courses taken with the “FOL-C” general education attribute to span at least two terms";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{given: courses, where: { semester: Interim }, what: terms, do: count >= 3}").unwrap();
	let expected = "have enough courses taken during Interim semesters to span at least three terms";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_inline_given_requirements_what_courses() {
	let input: Rule =
            serde_yaml::from_str(&"{given: these requirements, requirements: [{requirement: Core}, {requirement: Modern}], what: credits, do: sum >= 1}").unwrap();
	let expected = "have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. there must be at least one credit\n";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
            serde_yaml::from_str(&"{given: these requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { gereqs: FOL-C }, what: credits, do: sum >= 1}").unwrap();
	let expected = "have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken with the “FOL-C” general education attribute,
3. there must be at least one credit\n";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
            serde_yaml::from_str(&"{given: these requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { semester: Interim }, what: credits, do: sum >= 3}")
                .unwrap();
	let expected = "have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during Interim semesters,
3. there must be at least three credits\n";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
            serde_yaml::from_str(&"{given: these requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { semester: Fall }, what: credits, do: sum >= 10}").unwrap();
	let expected = "have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during Fall semesters,
3. there must be at least ten credits\n";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
            serde_yaml::from_str(&"{given: these requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { year: '2012' }, what: credits, do: sum >= 1}").unwrap();
	let expected = "have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during the 2012-13 academic year,
3. there must be at least one credit\n";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
            serde_yaml::from_str(&"{given: these requirements, requirements: [{requirement: Core}, {requirement: Modern}], where: { institution: St. Olaf College }, what: credits, do: sum >= 17}").unwrap();
	let expected = "have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken at St. Olaf College,
3. there must be at least 17 credits\n";
	assert_eq!(expected, input.print().unwrap());
}
