use super::*;
use crate::rules::{course, given};
use crate::traits::print::Print;
use indexmap::indexmap;

#[test]
fn deserialize() {
	let data = r#"---
given: courses
where: { semester: Interim }
what: courses
name: Interim Courses"#;

	let filter: filter::Clause = indexmap! {
		"semester".into() => "Interim".parse::<filter::WrappedValue>().unwrap(),
	};

	let expected = SaveBlock {
		name: "Interim Courses".to_string(),
		given: Given::AllCourses,
		limit: None,
		filter: Some(filter),
		what: Some(What::Courses),
		action: None,
	};

	let actual: SaveBlock = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn deserialize_dance() {
	let data = r#"---
given: these courses
courses: [DANCE 399]
repeats: last
where: {year: graduation-year, semester: Fall}
name: "Senior Dance Seminars""#;

	let filter: filter::Clause = indexmap! {
		"year".into() => "graduation-year".parse::<filter::WrappedValue>().unwrap(),
		"semester".into() => "Fall".parse::<filter::WrappedValue>().unwrap(),
	};

	let expected = SaveBlock {
		name: "Senior Dance Seminars".to_string(),
		given: Given::TheseCourses {
			courses: vec![given::CourseRule::Value(course::Rule {
				course: "DANCE 399".to_string(),
				..Default::default()
			})],
			repeats: given::RepeatMode::Last,
		},
		limit: None,
		filter: Some(filter),
		what: None,
		action: None,
	};

	let actual: SaveBlock = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}

#[test]
fn pretty_print() {
	let input: SaveBlock =
		serde_yaml::from_str(&"{name: Interim, given: courses, where: {semester: Interim}}").unwrap();
	let expected = "Given the subset of courses from your transcript, limited to only courses taken during Interim semesters, as “Interim”:

| “Interim” |
| --------- |
| (todo: list matching courses here) |
";
	assert_eq!(expected, input.print().unwrap());

	let input: SaveBlock = serde_yaml::from_str(&"{name: Interim, given: courses}").unwrap();
	let expected = "Given the courses from your transcript as “Interim”:

| “Interim” |
| --------- |
| (todo: list all??? courses here???) |
";
	assert_eq!(expected, input.print().unwrap());

	let input: SaveBlock =
		serde_yaml::from_str(&"{name: Interim, given: these courses, courses: [THEAT 244], repeats: all}").unwrap();
	let expected =
		"Given the intersection between this set of courses and the courses from your transcript, as “Interim”:

| “Interim” | Transcript |
| --------- | ---------- |
| THEAT 244 | (todo: fill out if match) |
";
	assert_eq!(expected, input.print().unwrap());

	let input: SaveBlock = serde_yaml::from_str(&"{name: Interim, given: save, save: Before}").unwrap();
	let expected = "Given the subset named “Before”, as “Interim”:

| “Interim” |
| --------- |
| (todo: list all??? courses here???) |
";
	assert_eq!(expected, input.print().unwrap());

	let input: SaveBlock =
		serde_yaml::from_str(&"{name: Interim, given: save, save: Before, where: {semester: Interim}}").unwrap();
	let expected = "Given the subset named “Before”, limited it to only courses taken during Interim semesters, as “Interim”:

| “Interim” |
| --------- |
| (todo: list matching courses here) |
";
	assert_eq!(expected, input.print().unwrap());
}
