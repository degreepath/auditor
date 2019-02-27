use super::*;
use crate::traits::print::Print;
use insta::{assert_debug_snapshot_matches, assert_snapshot_matches, assert_yaml_snapshot_matches};

#[test]
fn serialize_count_of_any() {
	let data = Rule {
		count: Counter::Any,
		of: vec![],
	};

	assert_yaml_snapshot_matches!("serialize_count_of_any", data);
}

#[test]
fn deserialize_count_of_any() {
	let data = "---
count: any
of: []";

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_debug_snapshot_matches!("deserialize_count_of_any", actual);
}

#[test]
fn serialize_count_of_all() {
	let data = Rule {
		count: Counter::All,
		of: vec![],
	};

	assert_yaml_snapshot_matches!("serialize_count_of_all", data);
}

#[test]
fn deserialize_count_of_all() {
	let data = "---
count: all
of: []";

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_debug_snapshot_matches!("deserialize_count_of_all", actual);
}

#[test]
fn serialize_count_of_number() {
	let data = Rule {
		count: Counter::Number(6),
		of: vec![],
	};

	assert_yaml_snapshot_matches!("serialize_count_of_number", data);
}

#[test]
fn deserialize_count_of_number() {
	let data = "---
count: 6
of: []";

	let actual: Rule = serde_yaml::from_str(&data).unwrap();
	assert_debug_snapshot_matches!("deserialize_count_of_number", actual);
}

#[test]
fn pretty_print_inline() {
	let s = "{count: any, of: [CS 111]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take CS 111");

	let s = "{count: any, of: [{requirement: Core}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"complete the “Core” requirement");

	let s = "{count: any, of: [{both: [CS 111, CS 121]}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take both CS 111 and CS 121");

	let s = "{count: all, of: [CS 111, CS 121]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take both CS 111 and CS 121");

	let s = "{count: any, of: [CS 111, CS 121]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take either CS 111 or CS 121");

	let s = "{count: any, of: [CS 111, CS 121, CS 131]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take one course from among CS 111, CS 121, or CS 131");

	let s = "{count: all, of: [CS 111, CS 121, CS 131]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"take CS 111, CS 121, and CS 131");

	let s = "{count: all, of: [{requirement: A}, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"complete both the “A” and “B” requirements");

	let s = "{count: all, of: [{requirement: A}, {requirement: B}, {requirement: C}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"complete “A”, “B”, and “C”");

	let s = "{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"complete one requirement from among “A”, “B”, or “C”");

	let s = "{count: 2, of: [{requirement: A}, {requirement: B}, {requirement: C}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @"complete two requirements from among “A”, “B”, or “C”");
}

#[test]
fn all_two_course_one_requirement() {
	let expected = "take CS 111 and CS 121, and complete the “B” requirement";

	let s = "{count: all, of: [CS 111, CS 121, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: all, of: [CS 111, {requirement: B}, CS 121]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: all, of: [{requirement: B}, CS 111, CS 121]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);
}

#[test]
fn any_two_course_one_requirement() {
	let expected = "take CS 111 or CS 121, or complete the “B” requirement";

	let s = "{count: any, of: [CS 111, CS 121, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: any, of: [CS 111, {requirement: B}, CS 121]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: any, of: [{requirement: B}, CS 111, CS 121]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);
}

#[test]
fn all_two_requirement_one_course() {
	let expected = "take CS 111, and complete both the “A” and “B” requirements";

	let s = "{count: all, of: [CS 111, {requirement: A}, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: all, of: [{requirement: A}, CS 111, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: all, of: [{requirement: A}, {requirement: B}, CS 111]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);
}

#[test]
fn any_two_requirement_one_course() {
	let expected = "take CS 111, or complete either the “A” or “B” requirements";

	let s = "{count: any, of: [CS 111, {requirement: A}, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: any, of: [{requirement: A}, CS 111, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: any, of: [{requirement: A}, {requirement: B}, CS 111]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);
}

#[test]
fn two_of_one_requirement_two_course() {
	let expected = "complete or take two requirements or courses from among CS 111, “A”, or “B”";

	let s = "{count: 2, of: [CS 111, {requirement: A}, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: 2, of: [{requirement: A}, CS 111, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: 2, of: [{requirement: A}, {requirement: B}, CS 111]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);
}

#[test]
fn two_of_two_requirement_one_course() {
	let expected = "complete or take two requirements or courses from among CS 111, “A”, or “B”";

	let s = "{count: 2, of: [CS 111, {requirement: A}, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: 2, of: [{requirement: A}, CS 111, {requirement: B}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);

	let s = "{count: 2, of: [{requirement: A}, {requirement: B}, CS 111]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_eq!(input.print().unwrap(), expected);
}

#[test]
fn both_either_requirement() {
	let s = "{count: all, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"do all of the following:

- take both CS 111 and CS 251
- complete either the “A” or “B” requirement
- complete the “C” requirement"###);
}

#[test]
fn pretty_print_block() {
	let s = "{count: any, of: [CS 111, CS 121, CS 124, CS 125]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"take one of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125"###);

	let s = "{count: 1, of: [CS 111, CS 121, CS 124, CS 125]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"take one of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125"###);

	let s = "{count: all, of: [CS 111, CS 121, CS 124, CS 125]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"take all of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125"###);

	let s = "{count: 4, of: [CS 111, CS 121, CS 124, CS 125]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"take all of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125"###);

	let s = "{count: 2, of: [CS 111, CS 121, CS 124, CS 125]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"take two of the following courses:

- CS 111
- CS 121
- CS 124
- CS 125"###);

	let s = "{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"complete one of the following requirements:

- “A”
- “B”
- “C”
- “D”"###);

	let s = "{count: any, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"complete one of the following requirements:

- “A”
- “B”
- “C”
- “D”"###);

	let s = "{count: 2, of: [{requirement: A}, {requirement: B}, {requirement: C}, {requirement: D}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"complete two from among the following requirements:

- “A”
- “B”
- “C”
- “D”"###);

	let s = "{count: 2, of: [{both: [CS 111, CS 251]}, {requirement: A}, {requirement: B}, {requirement: C}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"do two from among the following:

- take both CS 111 and CS 251
- complete the “A” requirement
- complete the “B” requirement
- complete the “C” requirement"###);

	let s = "{count: any, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"do one of the following:

- take both CS 111 and CS 251
- complete either the “A” or “B” requirement
- complete the “C” requirement"###);

	let s =
		"{count: 2, of: [{both: [CS 111, CS 251]}, {either: [{requirement: A}, {requirement: B}]}, {requirement: C}]}";
	let input: Rule = serde_yaml::from_str(&s).unwrap();
	assert_snapshot_matches!(input.print().unwrap(), @r###"do two from among the following:

- take both CS 111 and CS 251
- complete either the “A” or “B” requirement
- complete the “C” requirement"###);
}
