use super::filter;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Limiter {
	#[serde(rename = "where")]
	filter: filter::Clause,
	at_most: u64,
}

#[cfg(test)]
mod tests {
	use super::*;

	#[test]
	fn serialize_level100() {
		let clause: filter::Clause = hashmap! {
			"level".into() => "100".parse::<filter::WrappedValue>().unwrap(),
		};

		let data = Limiter {
			filter: clause,
			at_most: 2,
		};

		let expected = r#"---
where:
  level: "= 100"
at_most: 2"#;

		let actual = serde_yaml::to_string(&data).unwrap();

		assert_eq!(actual, expected);
	}

	#[test]
	fn serialize_not_math() {
		let clause: filter::Clause = hashmap! {
			"department".into() => "! MATH".parse::<filter::WrappedValue>().unwrap(),
		};

		let data = Limiter {
			filter: clause,
			at_most: 2,
		};

		let expected = r#"---
where:
  department: "! MATH"
at_most: 2"#;

		let actual = serde_yaml::to_string(&data).unwrap();

		assert_eq!(actual, expected);
	}
}
