use super::*;
use crate::rules::given::action;
use crate::traits::print::Print;

#[test]
fn deserialize() {
	let data = r#"---
do: >
  "first BTS-T course" < "last EIN course""#;

	let expected_struct = Rule {
		action: Action {
			lhs: action::Value::String("first BTS-T course".to_string()),
			op: Some(action::Operator::LessThan),
			rhs: Some(action::Value::String("last EIN course".to_string())),
		},
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(expected_struct, actual);
}

#[test]
fn pretty_print() {
	let data = r#"---
do: >
  "first BTS-T course" < "last EIN course""#;

	let expected = "ensure that the computed result of the subset “first BTS-T course” is less than the computed result of the subset “last EIN course”";

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(expected, actual.print().unwrap());
}

#[test]
fn pretty_print_gte() {
	let data = r#"---
do: >
  "first BTS-T course" >= "last EIN course""#;

	let expected = "ensure that the computed result of the subset “first BTS-T course” is greater than or equal to the computed result of the subset “last EIN course”";

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(expected, actual.print().unwrap());
}

#[test]
#[ignore]
fn pretty_print_block() {
	let input: Rule = serde_yaml::from_str(
		&"---
given: these courses
courses: [DANCE 399]
where: {year: graduation-year, semester: Fall}
name: $dance_seminars
label: Senior Dance Seminars
",
	)
	.unwrap();
	let expected = "Given the intersection between the following potential courses and your transcript, but limiting your transcript to only the courses taken in the Fall of your Senior year, as “Senior Dance Seminars”:

| Potential | “Senior Dance Seminars” |
| --------- | ----------------------- |
| DANCE 399 | DANCE 399 2015-1        |";
	assert_eq!(expected, input.print().unwrap());
}
