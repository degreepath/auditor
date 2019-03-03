use super::*;
use crate::rules::{req_ref, Rule as AnyRule};
use crate::traits::print::Print;
use insta::assert_yaml_snapshot_matches;

#[test]
fn serialize() {
	let input = Rule {
		both: (
			Box::new(AnyRule::Requirement(req_ref::Rule {
				name: String::from("Name"),
				optional: false,
			})),
			Box::new(AnyRule::Requirement(req_ref::Rule {
				name: String::from("Name 2"),
				optional: false,
			})),
		),
	};

	assert_yaml_snapshot_matches!(input, @r###"both:
  - type: requirement
    name: Name
    optional: false
  - type: requirement
    name: Name 2
    optional: false"###);
}

#[test]
fn deserialize() {
	let input = "---
both:
  - type: requirement
    name: Name
    optional: false
  - type: requirement
    name: Name 2
    optional: false";

	let expected_struct = Rule {
		both: (
			Box::new(AnyRule::Requirement(req_ref::Rule {
				name: String::from("Name"),
				optional: false,
			})),
			Box::new(AnyRule::Requirement(req_ref::Rule {
				name: String::from("Name 2"),
				optional: false,
			})),
		),
	};

	let actual: Rule = serde_yaml::from_str(&input).unwrap();
	assert_eq!(actual, expected_struct);
}

#[test]
fn pretty_print() {
	let input: Rule =
		serde_yaml::from_str(&"{both: [{type: requirement, name: A}, {type: requirement, name: B}]}").unwrap();
	let expected = "complete both the “A” and “B” requirements";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [CS 111, CS 121]}").unwrap();
	let expected = "take both CS 111 and CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [CS 121, {type: requirement, name: A}]}").unwrap();
	let expected = "take CS 121 and complete the “A” requirement";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [{type: requirement, name: A}, CS 121]}").unwrap();
	let expected = "complete the “A” requirement and take CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [CS 121, {type: both, both: [CS 251, CS 130]}]}").unwrap();
	let expected = "both take CS 121 and take both CS 251 and CS 130";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{both: [{type: requirement, name: A}, {type: both, both: [CS 251, CS 130]}]}").unwrap();
	let expected = "both complete the “A” requirement and take both CS 251 and CS 130";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{both: [{type: given, given: courses, what: courses, do: count >= 3}, CS 121]}")
			.unwrap();
	let expected = "both take at least three courses and take CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{both: [{type: given, given: courses, what: courses, do: count >= 3}, {type: requirement, name: A}]}",
	)
	.unwrap();
	let expected = "both take at least three courses and complete the “A” requirement";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [{type: given, given: courses, what: courses, do: count >= 3}, {type: given, given: these-courses, courses: [THEAT 233], repeats: all, what: courses, do: count >= 4}]}").unwrap();
	let expected = "both:

- take at least three courses

- and take THEAT 233 at least four times";
	assert_eq!(expected, input.print().unwrap());
}
