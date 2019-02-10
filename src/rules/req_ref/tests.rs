use super::*;
use crate::traits::print::Print;

#[test]
fn serialize() {
	let data = Rule {
		requirement: String::from("Name"),
		optional: false,
	};
	let expected = "---
requirement: Name
optional: false";

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize() {
	let data = "---
requirement: Name
optional: false";
	let expected = Rule {
		requirement: String::from("Name"),
		optional: false,
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn deserialize_with_defaults() {
	let data = "---
requirement: Name";
	let expected = Rule {
		requirement: String::from("Name"),
		optional: false,
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}

#[test]
fn pretty_print() {
	let input = Rule {
		requirement: "Core".into(),
		optional: false,
	};
	let expected = "“Core”";
	assert_eq!(expected, input.print().unwrap());

	let input = Rule {
		requirement: "Core".into(),
		optional: true,
	};
	let expected = "“Core” (optional)";
	assert_eq!(expected, input.print().unwrap());
}
