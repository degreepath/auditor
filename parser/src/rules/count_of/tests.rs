use super::*;
use crate::traits::print::Print;

#[test]
fn serialize_count_of_any() {
	let data = Rule {
		count: Counter::Any,
		of: vec![],
		surplus: None,
		limit: None,
	};

	let expected_str = "---
count: any
of: []
surplus: ~
limit: ~";

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected_str);
}

#[test]
fn deserialize_count_of_any() {
	let data = "---
count: any
of: []
surplus: ~
limit: ~";

	let expected_struct = Rule {
		count: Counter::Any,
		of: vec![],
		surplus: None,
		limit: None,
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected_struct);
}

#[test]
fn serialize_count_of_all() {
	let data = Rule {
		count: Counter::All,
		of: vec![],
		surplus: None,
		limit: None,
	};

	let expected_str = "---
count: all
of: []
surplus: ~
limit: ~";

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected_str);
}

#[test]
fn deserialize_count_of_all() {
	let data = "---
count: all
of: []
surplus: ~
limit: ~";

	let expected_struct = Rule {
		count: Counter::All,
		of: vec![],
		surplus: None,
		limit: None,
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected_struct);
}

#[test]
fn serialize_count_of_number() {
	let data = Rule {
		count: Counter::Number(6),
		of: vec![],
		surplus: None,
		limit: None,
	};

	let expected_str = "---
count: 6
of: []
surplus: ~
limit: ~";

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected_str);
}

#[test]
fn deserialize_count_of_number() {
	let data = "---
count: 6
of: []
surplus: ~
limit: ~";

	let expected_struct = Rule {
		count: Counter::Number(6),
		of: vec![],
		surplus: None,
		limit: None,
	};

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected_struct);
}

#[test]
fn pretty_print_inline() {
	let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111]}").unwrap();
	let expected = "take CS 111";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [{requirement: Core}]}").unwrap();
	let expected = "complete the “Core” requirement";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [{both: [CS 111, CS 121]}]}").unwrap();
	let expected = "take both CS 111 and CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, CS 121]}").unwrap();
	let expected = "take both CS 111 and CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, CS 121]}").unwrap();
	let expected = "take either CS 111 or CS 121";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, CS 121, CS 131]}").unwrap();
	let expected = "take one course from among CS 111, CS 121, or CS 131";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, CS 121, CS 131]}").unwrap();
	let expected = "take CS 111, CS 121, and CS 131";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [{requirement: A}, {requirement: B}]}").unwrap();
	let expected = "complete both the “A” and “B” requirements";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{count: all, of: [{requirement: A}, {requirement: B}, {requirement: C}]}").unwrap();
	let expected = "complete “A”, “B”, and “C”";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}]}").unwrap();
	let expected = "complete one requirement from among “A”, “B”, or “C”";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
		serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, {requirement: B}, {requirement: C}]}").unwrap();
	let expected = "complete two requirements from among “A”, “B”, or “C”";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn all_two_course_one_requirement() {
	let expected = "take CS 111 and CS 121, and complete the “B” requirement";

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, CS 121, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, {requirement: B}, CS 121]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [{requirement: B}, CS 111, CS 121]}").unwrap();
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn any_two_course_one_requirement() {
	let expected = "take CS 111 or CS 121, or complete the “B” requirement";

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, CS 121, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, {requirement: B}, CS 121]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [{requirement: B}, CS 111, CS 121]}").unwrap();
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn all_two_requirement_one_course() {
	let expected = "take CS 111, and complete both the “A” and “B” requirements";

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, {requirement: A}, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [{requirement: A}, CS 111, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [{requirement: A}, {requirement: B}, CS 111]}").unwrap();
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn any_two_requirement_one_course() {
	let expected = "take CS 111, or complete either the “A” or “B” requirements";

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, {requirement: A}, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [{requirement: A}, CS 111, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: any, of: [{requirement: A}, {requirement: B}, CS 111]}").unwrap();
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn two_of_one_requirement_two_course() {
	let expected = "complete or take two requirements or courses from among CS 111, “A”, or “B”";

	let input: Rule = serde_yaml::from_str(&"{count: 2, of: [CS 111, {requirement: A}, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, CS 111, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, {requirement: B}, CS 111]}").unwrap();
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn two_of_two_requirement_one_course() {
	let expected = "complete or take two requirements or courses from among CS 111, “A”, or “B”";

	let input: Rule = serde_yaml::from_str(&"{count: 2, of: [CS 111, {requirement: A}, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, CS 111, {requirement: B}]}").unwrap();
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: 2, of: [{requirement: A}, {requirement: B}, CS 111]}").unwrap();
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn both_either_requirement() {
	let input: Rule =
            serde_yaml::from_str(&"{count: all, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}").unwrap();
	let expected = "do all of the following:

- take both CS 111 and CS 251
- complete either the “A” or “B” requirement
- complete the “C” requirement";
	assert_eq!(expected, input.print().unwrap());
}

#[test]
fn pretty_print_block() {
	let input: Rule = serde_yaml::from_str(&"{count: any, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
	let expected = "take one of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: 1, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
	let expected = "take one of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: all, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
	let expected = "take all of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: 4, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
	let expected = "take all of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(&"{count: 2, of: [CS 111, CS 121, CS 124, CS 125]}").unwrap();
	let expected = "take two of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}",
	)
	.unwrap();
	let expected = "complete one of the following requirements:

- “A”
- “B”
- “C”
- “D”";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}",
	)
	.unwrap();
	let expected = "complete one of the following requirements:

- “A”
- “B”
- “C”
- “D”";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{count: 2, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}",
	)
	.unwrap();
	let expected = "complete two from among the following requirements:

- “A”
- “B”
- “C”
- “D”";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{count: 2, of: [{both: [CS 111, CS 251]}, {requirement: A}, {requirement: B}, {requirement: C}]}",
	)
	.unwrap();
	let expected = "do two from among the following:

- take both CS 111 and CS 251
- complete the “A” requirement
- complete the “B” requirement
- complete the “C” requirement";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule =
            serde_yaml::from_str(&"{count: any, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}").unwrap();
	let expected = "do one of the following:

- take both CS 111 and CS 251
- complete either the “A” or “B” requirement
- complete the “C” requirement";
	assert_eq!(expected, input.print().unwrap());

	let input: Rule = serde_yaml::from_str(
		&"{count: 2, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}",
	)
	.unwrap();
	let expected = "do two from among the following:

- take both CS 111 and CS 251
- complete either the “A” or “B” requirement
- complete the “C” requirement";
	assert_eq!(expected, input.print().unwrap());
}
