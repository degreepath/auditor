use super::SaveBlock;
use crate::filter::CourseClause;
use crate::rules::given::{GivenCoursesWhatOptions, GivenForSaveBlock as Given};
use crate::rules::{course, given};
use crate::traits::print::Print;
use crate::value;

#[test]
fn deserialize() {
	let data = r#"---
given: courses
where: { semester: Interim }
what: courses
name: Interim Courses"#;

	let filter = CourseClause {
		semester: Some("Interim".parse::<value::WrappedValue<crate::student::Semester>>().unwrap()),
		..CourseClause::default()
	};

	let expected = SaveBlock {
		name: "Interim Courses".to_string(),
		given: Given::AllCourses {
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: None,
		filter: Some(filter),
		action: None,
	};

	let actual: SaveBlock = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_dance() {
	let data = r#"---
given: these-courses
courses: [DANCE 399]
repeats: last
where: {year: graduation-year, semester: Fall}
what: courses
name: "Senior Dance Seminars""#;

	let filter = CourseClause {
		year: Some("graduation-year".parse::<value::WrappedValue<crate::filter::ClassificationYear>>().unwrap()),
		semester: Some("Fall".parse::<value::WrappedValue<crate::student::Semester>>().unwrap()),
		..CourseClause::default()
	};

	let expected = SaveBlock {
		name: "Senior Dance Seminars".to_string(),
		given: Given::TheseCourses {
			courses: vec![given::CourseRule::Value(course::Rule {
				course: "DANCE 399".to_string(),
				..Default::default()
			})],
			repeats: given::RepeatMode::Last,
			what: GivenCoursesWhatOptions::Courses,
		},
		limit: None,
		filter: Some(filter),
		action: None,
	};

	let actual: SaveBlock = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn pretty_print() {
	let input = "{name: Interim, given: courses, where: {semester: Interim}, what: courses}";
	let input: SaveBlock = serde_yaml::from_str(&input).unwrap();
	let expected = "Given the subset of courses from your transcript, limited to only courses taken during Interim semesters, as “Interim”:

| “Interim” |
| --------- |
| (todo: list matching courses here) |
";
	assert_eq!(expected, input.print().unwrap());

	let input = "{name: Interim, given: courses, what: courses}";
	let input: SaveBlock = serde_yaml::from_str(&input).unwrap();
	let expected = "Given the courses from your transcript as “Interim”:

| “Interim” |
| --------- |
| (todo: list all??? courses here???) |
";
	assert_eq!(expected, input.print().unwrap());

	let input = "{name: Interim, given: these-courses, courses: [THEAT 244], repeats: all, what: courses}";
	let input: SaveBlock = serde_yaml::from_str(&input).unwrap();
	let expected =
		"Given the intersection between this set of courses and the courses from your transcript, as “Interim”:

| “Interim” | Transcript |
| --------- | ---------- |
| THEAT 244 | (todo: fill out if match) |
";
	assert_eq!(expected, input.print().unwrap());

	let input = "{name: Interim, given: save, what: courses, save: Before}";
	let input: SaveBlock = serde_yaml::from_str(&input).unwrap();
	let expected = "Given the subset named “Before”, as “Interim”:

| “Interim” |
| --------- |
| (todo: list all??? courses here???) |
";
	assert_eq!(expected, input.print().unwrap());

	let input = "{name: Interim, given: save, save: Before, where: {semester: Interim}, what: courses}";
	let input: SaveBlock = serde_yaml::from_str(&input).unwrap();
	let expected =
		"Given the subset named “Before”, limited it to only courses taken during Interim semesters, as “Interim”:

| “Interim” |
| --------- |
| (todo: list matching courses here) |
";
	assert_eq!(expected, input.print().unwrap());
}
