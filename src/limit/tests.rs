use super::Limiter;
use crate::filter;
use crate::value::WrappedValue;
use insta::assert_yaml_snapshot_matches;

#[test]
fn serialize_level100() {
	let clause = filter::CourseClause {
		level: Some("100".parse::<WrappedValue<u64>>().unwrap()),
		..filter::CourseClause::default()
	};

	let data = Limiter {
		filter: clause,
		at_most: 2,
	};

	assert_yaml_snapshot_matches!(data, @r###"---
at_most: 2
where:
  level:
    Single:
      EqualTo: 100"###);
}

#[test]
fn serialize_not_math() {
	let clause = filter::CourseClause {
		subject: Some("! MATH".parse::<WrappedValue<String>>().unwrap()),
		..filter::CourseClause::default()
	};

	let data = Limiter {
		filter: clause,
		at_most: 2,
	};

	assert_yaml_snapshot_matches!(data, @r###"---
at_most: 2
where:
  subject:
    Single:
      NotEqualTo: MATH"###);
}

#[test]
fn deserialize_level100() {
	let clause = filter::CourseClause {
		level: Some("100".parse::<WrappedValue<u64>>().unwrap()),
		..filter::CourseClause::default()
	};

	let expected = Limiter {
		filter: clause,
		at_most: 2,
	};

	let data = "{at_most: 2, where: {level: 100}}";
	let actual: Limiter = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);

	let data = r#"{at_most: 2, where: {level: "100"}}"#;
	let actual: Limiter = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected);
}
