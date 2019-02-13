use super::*;
use crate::action;
use crate::traits::print::Print;

#[test]
fn deserialize() {
	let data = r#"---
do: {lhs: "first BTS-T course", op: "<", rhs: "last EIN course"}"#;

	let expected_struct = Rule {
		action: LhsValueAction {
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
do: {lhs: "first BTS-T course", op: "<", rhs: "last EIN course"}"#;

	let expected = "ensure that the computed result of the subset “first BTS-T course” is less than the computed result of the subset “last EIN course”";

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(expected, actual.print().unwrap());
}

#[test]
fn pretty_print_gte() {
	let data = r#"---
do: {lhs: "first BTS-T course", op: ">=", rhs: "last EIN course"}"#;

	let expected = "ensure that the computed result of the subset “first BTS-T course” is greater than or equal to the computed result of the subset “last EIN course”";

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(expected, actual.print().unwrap());
}
