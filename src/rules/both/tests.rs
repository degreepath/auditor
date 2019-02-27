use super::*;
use crate::rules::{req_ref, Rule as AnyRule};
use crate::traits::print::Print;

#[test]
fn serialize() {
	let input = Rule {
		both: (
			Box::new(AnyRule::Requirement(req_ref::Rule {
				requirement: String::from("Name"),
				optional: false,
			})),
			Box::new(AnyRule::Requirement(req_ref::Rule {
				requirement: String::from("Name 2"),
				optional: false,
			})),
		),
	};

	let expected_str = "---
both:
  - requirement: Name
    optional: false
  - requirement: Name 2
    optional: false";

	let actual = serde_yaml::to_string(&input).unwrap();
	assert_eq!(actual, expected_str);
}

#[test]
fn deserialize() {
	let input = "---
both:
  - requirement: Name
    optional: false
  - requirement: Name 2
    optional: false";

	let expected_struct = Rule {
		both: (
			Box::new(AnyRule::Requirement(req_ref::Rule {
				requirement: String::from("Name"),
				optional: false,
			})),
			Box::new(AnyRule::Requirement(req_ref::Rule {
				requirement: String::from("Name 2"),
				optional: false,
			})),
		),
	};

	let actual: Rule = serde_yaml::from_str(&input).unwrap();
	assert_eq!(actual, expected_struct);
}

#[test]
fn pretty_print() {
	let input: Rule = serde_yaml::from_str(&"{both: [{requirement: A}, {requirement: B}]}").unwrap();
	let expected = "complete both the “A” and “B” requirements";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [CS 111, CS 121]}").unwrap();
	let expected = "take both CS 111 and CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [CS 121, {requirement: A}]}").unwrap();
	let expected = "take CS 121 and complete the “A” requirement";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [{requirement: A}, CS 121]}").unwrap();
	let expected = "complete the “A” requirement and take CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [CS 121, {both: [CS 251, CS 130]}]}").unwrap();
	let expected = "both take CS 121 and take both CS 251 and CS 130";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [{requirement: A}, {both: [CS 251, CS 130]}]}").unwrap();
	let expected = "both complete the “A” requirement and take both CS 251 and CS 130";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{both: [{given: courses, what: courses, do: count >= 3}, CS 121]}").unwrap();
	let expected = "both take at least three courses and take CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{both: [{given: courses, what: courses, do: count >= 3}, {requirement: A}]}").unwrap();
	let expected = "both take at least three courses and complete the “A” requirement";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{both: [{given: courses, what: courses, do: count >= 3}, {given: these-courses, courses: [THEAT 233], repeats: all, what: courses, do: count >= 4}]}").unwrap();
	let expected = "both:

- take at least three courses

- and take THEAT 233 at least four times";
	assert_eq!(expected, input.print().unwrap());
}
