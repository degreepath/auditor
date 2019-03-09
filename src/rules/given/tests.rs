use super::Rule;
use super::{AnyAction, CourseRule, GivenAreasWhatOptions, GivenCoursesWhatOptions, RepeatMode};
use crate::filter::{AreaClause, CourseClause};
use crate::rules::course;
use crate::traits::print::Print;
use crate::value;
use insta::{assert_ron_snapshot_matches, assert_snapshot_matches};
use pretty_assertions::assert_eq;
use value::{
	TaggedValue::{EqualTo, GreaterThan, GreaterThanEqualTo},
	WrappedValue::Single,
};

#[test]
fn serialize_all_courses() {
	let data = Rule::AllCourses {
		what: GivenCoursesWhatOptions::Courses,
		limit: Some(vec![]),
		filter: Some(CourseClause::default()),
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
	};

	assert_ron_snapshot_matches!("ser_all_courses", data);
}

#[test]
fn deserialize_all_courses() {
	let expected = Rule::AllCourses {
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		limit: Some(vec![]),
		filter: Some(CourseClause::default()),
	};

	let data = r#"---
given: courses
what: courses
limit: []
where: {}
action: {count: '> 2'}"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn serialize_these_courses() {
	let data = Rule::TheseCourses {
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
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		limit: Some(vec![]),
		filter: Some(CourseClause::default()),
	};

	assert_ron_snapshot_matches!("ser_these_courses_1", data);
}

#[test]
fn deserialize_these_courses() {
	let expected = Rule::TheseCourses {
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
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		limit: Some(vec![]),
		filter: Some(CourseClause::default()),
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
action: {count: '> 2'}"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn serialize_these_requirements() {
	let data = Rule::TheseRequirements {
		requirements: vec!["A Name 1".to_string(), "A Name 2".to_string()],
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		limit: Some(vec![]),
		filter: Some(CourseClause::default()),
	};

	assert_ron_snapshot_matches!("ser_these_reqs", data);
}

#[test]
fn deserialize_these_requirements() {
	let expected = Rule::TheseRequirements {
		requirements: vec!["A Name 1".to_string(), "A Name 2".to_string()],
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		limit: Some(vec![]),
		filter: Some(CourseClause::default()),
	};

	let data = r#"---
given: these-requirements
requirements:
  - A Name 1
  - A Name 2
what: courses
limit: []
where: {}
action: {count: '> 2'}"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn serialize_areas() {
	let data = Rule::Areas {
		what: GivenAreasWhatOptions::Areas,
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		filter: Some(AreaClause::default()),
	};

	assert_ron_snapshot_matches!("ser_areas", data);
}

#[test]
fn deserialize_areas() {
	let expected = Rule::Areas {
		what: GivenAreasWhatOptions::Areas,
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		filter: Some(AreaClause::default()),
	};

	let data = r#"---
given: areas
what: areas
limit: []
where: {}
action: {count: '> 2'}"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn serialize_save() {
	let data = Rule::NamedVariable {
		save: String::from("$my_var"),
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		limit: Some(vec![]),
		filter: Some(CourseClause::default()),
	};

	assert_ron_snapshot_matches!("ser_save", data);
}

#[test]
fn deserialize_save() {
	let expected = Rule::NamedVariable {
		save: String::from("$my_var"),
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(2)))),
		limit: Some(vec![]),
		filter: Some(CourseClause::default()),
	};

	let data = r#"---
given: save
save: $my_var
what: courses
limit: []
where: {}
action: {count: '> 2'}"#;

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_save_ba_interim() {
	let data = r#"---
given: save
save: $interim_courses
what: courses
action: {count: '>= 3'}"#;

	let expected = Rule::NamedVariable {
		save: String::from("$interim_courses"),
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThanEqualTo(3)))),
		limit: None,
		filter: None,
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_gereqs_single() {
	let data = r#"{where: {gereqs: 'FYW'}, given: courses, what: courses, action: {count: '> 1'}}"#;

	let expected = CourseClause {
		gereqs: Some(Single(EqualTo("FYW".to_string()))),
		..CourseClause::default()
	};
	let expected = Rule::AllCourses {
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(1)))),
		limit: None,
		filter: Some(expected),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_gereqs_or() {
	use value::{TaggedValue, WrappedValue};
	let data = r#"{where: {gereqs: 'MCD | MCG'}, given: courses, what: courses, action: {count: '> 1'}}"#;

	let expected = CourseClause {
		gereqs: Some(WrappedValue::Or(vec![
			TaggedValue::EqualTo("MCD".to_string()),
			TaggedValue::EqualTo("MCG".to_string()),
		])),
		..CourseClause::default()
	};
	let expected = Rule::AllCourses {
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(1)))),
		limit: None,
		filter: Some(expected),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_level_gte() {
	let data = r#"{where: {level: '>= 200'}, given: courses, what: courses, action: {count: '> 1'}}"#;

	let expected = CourseClause {
		level: Some(Single(GreaterThanEqualTo(200))),
		..CourseClause::default()
	};
	let expected = Rule::AllCourses {
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(1)))),
		limit: None,
		filter: Some(expected),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_graded_pn() {
	let data = r#"{where: {graded: pn}, given: courses, what: courses, action: {count: '> 1'}}"#;

	let expected = CourseClause {
		graded: Some(Single(EqualTo(crate::filter::GradeOption::Pn))),
		..CourseClause::default()
	};
	let expected = Rule::AllCourses {
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(1)))),
		limit: None,
		filter: Some(expected),
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_filter_graded_graded() {
	use crate::value::{TaggedValue, WrappedValue};

	let expected = CourseClause {
		graded: Some(Single(EqualTo(crate::filter::GradeOption::Graded))),
		grade: Some(WrappedValue::Single(TaggedValue::GreaterThanEqualTo(
			crate::grade::Grade::C,
		))),
		..CourseClause::default()
	};
	let expected = Rule::AllCourses {
		what: GivenCoursesWhatOptions::Courses,
		action: Some(AnyAction::Count(Single(GreaterThan(1)))),
		limit: None,
		filter: Some(expected),
	};

	let data = r#"{where: {graded: graded, grade: '>= 2.0'}, given: courses, what: courses, action: {count: '> 1'}}"#;
	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);

	let data = r#"{where: {graded: graded, grade: '>= C'}, given: courses, what: courses, action: {count: '> 1'}}"#;
	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

fn parse_rule(s: &str) -> Rule {
	serde_yaml::from_str(s).unwrap()
}

#[test]
fn pretty_print_inline() {
	let s = "{given: courses, what: courses, action: {count: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take at least one course");
}

#[test]
fn pretty_print_inline_filters() {
	let s = "{given: courses, where: {gereqs: FOL-C}, what: courses, action: {count: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take at least one course with the “FOL-C” general education attribute");

	let s = "{given: courses, where: {gereqs: SPM}, what: distinct-courses, action: {count: '>= 2'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take at least two distinct courses with the “SPM” general education attribute");
}

#[test]
fn pretty_print_inline_repeats() {
	let s = "{given: these-courses, repeats: all, courses: [THEAT 233], what: courses, action: {count: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take THEAT 233 at least one time");

	let s = "{given: these-courses, repeats: all, courses: [THEAT 233], what: courses, action: {count: '>= 4'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take THEAT 233 at least four times");

	let s =
		"{given: these-courses, repeats: all, courses: [THEAT 233, THEAT 253], what: courses, action: {count: '>= 4'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take a combination of THEAT 233 and THEAT 253 at least four times");

	let s = "{given: these-courses, repeats: all, courses: [AMST 205, AMST 206, AMST 207, AMST 208, AMST 209, AMST 210], what: courses, action: {count: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @r###"take at least one of the following courses:

- AMST 205
- AMST 206
- AMST 207
- AMST 208
- AMST 209
- AMST 210"###);

	let s = "{given: these-courses, repeats: all, courses: [THEAT 233], what: credits, action: {sum: '>= 4'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take THEAT 233 enough times to yield at least 4.00 credits");

	let s = "{given: these-courses, repeats: first, courses: [THEAT 233], what: courses, action: {count: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take THEAT 233");

	let s = "{given: these-courses, repeats: first, courses: [THEAT 233, THEAT 253], what: courses, action: {count: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take either THEAT 233 or THEAT 253");

	let s = "{given: these-courses, repeats: first, courses: [THEAT 233, THEAT 253], what: courses, action: {count: '>= 2'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"take both THEAT 233 and THEAT 253");
}

#[test]
fn pretty_print_inline_credits() {
	let s = "{given: courses, where: {gereqs: FOL-C}, what: credits, action: {sum: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken with the “FOL-C” general education attribute to obtain at least 1.00 credit");

	let s = "{given: courses, where: {semester: Interim}, what: credits, action: {sum: '>= 3'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during Interim semesters to obtain at least 3.00 credits");

	let s = "{given: courses, where: {semester: Fall}, what: credits, action: {sum: '>= 10'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during Fall semesters to obtain at least 10 credits");

	let s = "{given: courses, where: {semester: Fall | Interim}, what: credits, action: {sum: '>= 10'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during a Fall or Interim semester to obtain at least 10 credits");

	let s = "{given: courses, where: {year: 'junior-year'}, what: credits, action: {sum: '>= 3'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during your junior year to obtain at least 3.00 credits");

	let s = "{given: courses, where: {institution: St. Olaf College}, what: credits, action: {sum: '>= 17'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken at St. Olaf College to obtain at least 17 credits");
}

#[test]
fn pretty_print_inline_subjects() {
	let s = "{given: courses, where: {gereqs: FOL-C}, what: subjects, action: {count: '>= 2'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken with the “FOL-C” general education attribute to span at least two departments");

	let s = "{given: courses, where: {semester: Interim}, what: subjects, action: {count: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken during Interim semesters to span at least one department");

	let s = "{given: courses, where: {subject: '! MATH'}, what: subjects, action: {count: '>= 2'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have enough courses taken outside of the MATH subject code to span at least two departments");
}

#[test]
fn pretty_print_inline_grades() {
	let s = "{given: courses, where: { gereqs: FOL-C }, what: grades, action: {average: '>= 2.0'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"maintain an average GPA at or above 2.00 from courses taken with the “FOL-C” general education attribute");

	let s = "{given: courses, where: { semester: Interim }, what: grades, action: {average: '>= 3.0'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"maintain an average GPA at or above 3.00 from courses taken during Interim semesters");
}

#[test]
fn pretty_print_inline_terms() {
	let s = "{given: courses, where: { gereqs: FOL-C }, what: terms, action: {count: '>= 2'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have taken enough courses with the “FOL-C” general education attribute to span at least two terms");

	let s = "{given: courses, where: { semester: Interim }, what: terms, action: {count: '>= 3'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have taken enough courses during Interim semesters to span at least three terms");
}

#[test]
fn pretty_print_inline_given_requirements_what_courses() {
	let s = "{given: these-requirements, requirements: [Core, Modern], what: credits, action: {sum: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. there must be at least 1.00 credit
"###);

	let s = "{given: these-requirements, requirements: [Core, Modern], where: { gereqs: FOL-C }, what: credits, action: {sum: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken with the “FOL-C” general education attribute,
3. there must be at least 1.00 credit
"###);

	let s = "{given: these-requirements, requirements: [Core, Modern], where: { semester: Interim }, what: credits, action: {sum: '>= 3'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during Interim semesters,
3. there must be at least 3.00 credits
"###);

	let s = "{given: these-requirements, requirements: [Core, Modern], where: { semester: Fall }, what: credits, action: {sum: '>= 10'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during Fall semesters,
3. there must be at least 10 credits
"###);

	let s = "{given: these-requirements, requirements: [Core, Modern], where: { year: 'junior-year' }, what: credits, action: {sum: '>= 1'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken during your junior year,
3. there must be at least 1.00 credit
");

	let s = "{given: these-requirements, requirements: [Core, Modern], where: { institution: St. Olaf College }, what: credits, action: {sum: '>= 17'}}";
	let input = parse_rule(&s);
	assert_snapshot_matches!(input.print().unwrap(), @r###"have the following be true:

1. given the results of the “Core” and “Modern” requirements,
2. restricted to only courses taken at St. Olaf College,
3. there must be at least 17 credits
"###);
}
