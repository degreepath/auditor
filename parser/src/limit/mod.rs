use super::filter;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Limiter {
	#[serde(rename = "where", deserialize_with = "filter::deserialize_with_no_option")]
	filter: filter::Clause,
	at_most: u64,
}

#[cfg(test)]
mod tests {
	use super::*;

	#[test]
	fn serialize_level100() {
		let clause: filter::Clause = btreemap! {
			"level".into() => "100".parse::<filter::WrappedValue>().unwrap(),
		};

		let data = Limiter {
			filter: clause,
			at_most: 2,
		};

		let expected = r#"---
where:
  level:
    Single:
      op: EqualTo
      value:
        Integer: 100
at_most: 2"#;

		let actual = serde_yaml::to_string(&data).unwrap();

		assert_eq!(actual, expected);
	}

	#[test]
	fn serialize_not_math() {
		let clause: filter::Clause = btreemap! {
			"department".into() => "! MATH".parse::<filter::WrappedValue>().unwrap(),
		};

		let data = Limiter {
			filter: clause,
			at_most: 2,
		};

		let expected = r#"---
where:
  department:
    Single:
      op: NotEqualTo
      value:
        String: MATH
at_most: 2"#;

		let actual = serde_yaml::to_string(&data).unwrap();

		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_level100() {
		let clause: filter::Clause = btreemap! {
			"level".into() => "100".parse::<filter::WrappedValue>().unwrap(),
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
	}
}
