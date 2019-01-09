use super::filter;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Limiter {
    #[serde(rename = "where")]
    filter: filter::Clause,
    at_most: i32,
}

#[cfg(test)]
mod tests {
	use super::*;

	#[test]
	fn serialize_level100() {
		let mut clause = filter::Clause::new();
		clause.insert("level".to_string(), 100.into());

		let data = Limiter {
			filter: clause,
			at_most: 2,
		};

		let expected = r#"---
where:
  level: 100
at_most: 2"#;

		let actual = serde_yaml::to_string(&data).unwrap();

		assert_eq!(actual, expected);
	}

	#[test]
	fn serialize_not_math() {
		let mut clause = filter::Clause::new();
		clause.insert("department".to_string(), "! MATH".into());

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
