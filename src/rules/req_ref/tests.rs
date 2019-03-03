use super::*;
use crate::traits::print::Print;
use pretty_assertions::assert_eq;

#[test]
fn serialize() {
	let data = Rule {
		name: String::from("Name"),
		optional: false,
	};
	let expected = "---
name: Name
optional: false";

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize() {
	let data = "---
name: Name
optional: false";
	let expected = Rule {
		name: String::from("Name"),
		optional: false,
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_with_defaults() {
	let data = "---
name: Name";
	let expected = Rule {
		name: String::from("Name"),
		optional: false,
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn pretty_print() {
	let input = Rule {
		name: "Core".into(),
		optional: false,
	};
	let expected = "“Core”";
	assert_eq!(expected, input.print().unwrap());

	let input = Rule {
		name: "Core".into(),
		optional: true,
	};
	let expected = "“Core” (optional)";
	assert_eq!(expected, input.print().unwrap());
}
