use super::*;
use crate::student::Semester;
use crate::traits::print::Print;
use insta::assert_snapshot_matches;

#[test]
fn serialize() {
	let data = Rule {
		course: "STAT 214".to_string(),
		..Default::default()
	};

	let expected_str = "---
course: STAT 214";

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected_str);
}

#[test]
fn serialize_expanded() {
	let data = Rule {
		course: "STAT 214".to_string(),
		year: Some(2014),
		semester: Some(Semester::Summer1),
		..Default::default()
	};

	let expected_str = "---
course: STAT 214
grade: ~
section: ~
year: 2014
semester: Summer Session 1
lab: ~
can_match_used: ~";

	let actual = serde_yaml::to_string(&data).unwrap();
	assert_eq!(actual, expected_str);

	let deserialized: Rule = serde_yaml::from_str(&actual).unwrap();
	assert_eq!(deserialized, data);
}

#[test]
fn deserialize_labelled() {
	let data = "---
course: STAT 214";

	let expected_struct = Rule {
		course: "STAT 214".to_string(),
		..Default::default()
	};

	let deserialized: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(deserialized, expected_struct);
}

#[test]
fn deserialize_expanded() {
	let data = "---
course: STAT 214
section: ~
year: 2014
semester: Summer Session 1
lab: ~
can_match_used: ~";

	let expected_struct = Rule {
		course: "STAT 214".to_string(),
		year: Some(2014),
		semester: Some(Semester::Summer1),
		..Default::default()
	};

	let deserialized: Rule = serde_yaml::from_str(&data).unwrap();
	assert_eq!(deserialized, expected_struct);
}

#[test]
fn pretty_print() {
	let input = Rule {
		course: "DEPT 111".into(),
		..Default::default()
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111");

	let input = Rule {
		course: "DEPT 111".into(),
		semester: Some(Semester::Fall),
		year: Some(2015),
		..Default::default()
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111 (Fall 2015)");

	let input = Rule {
		course: "DEPT 111".into(),
		semester: Some(Semester::Fall),
		year: Some(2015),
		..Default::default()
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111 (Fall 2015)");

	let input = Rule {
		course: "DEPT 111".into(),
		semester: Some(Semester::Fall),
		..Default::default()
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111 (Fall)");

	let input = Rule {
		course: "DEPT 111".into(),
		year: Some(2015),
		..Default::default()
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111 (2015-16)");

	let input = Rule {
		course: "DEPT 111".into(),
		section: Some("A".to_string()),
		..Default::default()
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111A");

	let input = Rule {
		course: "DEPT 111".into(),
		lab: Some(true),
		..Default::default()
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111 (Lab)");

	let input = Rule {
		course: "DEPT 111".into(),
		semester: Some(Semester::Fall),
		year: Some(2015),
		lab: Some(true),
		..Default::default()
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111 (Lab; Fall 2015)");

	let input = Rule {
		course: "DEPT 111".into(),
		section: Some("A".to_string()),
		semester: Some(Semester::Fall),
		year: Some(2015),
		lab: Some(true),
		can_match_used: None,
		grade: None,
	};
	assert_snapshot_matches!(input.print().unwrap(), @"DEPT 111A (Lab; Fall 2015)");
}
