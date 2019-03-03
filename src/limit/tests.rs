use super::Limiter;
use crate::filter;
use crate::value::WrappedValue;

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

	let expected = r#"---
where:
  level:
    Single:
      EqualTo:
        Integer: 100
at_most: 2"#;

	let actual = serde_yaml::to_string(&data).unwrap();

	assert_eq!(actual, expected);
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

	let expected = r#"---
where:
  subject:
    Single:
      NotEqualTo:
        String: MATH
at_most: 2"#;

	let actual = serde_yaml::to_string(&data).unwrap();

	assert_eq!(actual, expected);
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

	let data = r#"---
where:
  level: "100"
at_most: 2"#;

	let actual: Limiter = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);

	let data = r#"---
where:
  level: 100
at_most: 2"#;

	let actual: Limiter = serde_yaml::from_str(&data).unwrap();

	assert_eq!(actual, expected);
}
