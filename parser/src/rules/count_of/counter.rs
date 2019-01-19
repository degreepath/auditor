use serde::de::{self, Deserialize, Deserializer, Visitor};
use serde::ser::{Serialize, Serializer};
use std::fmt;

#[derive(Debug, PartialEq, Clone)]
pub enum Counter {
	All,
	Any,
	Number(u64),
}

impl Counter {
	pub fn english(&self) -> String {
		match &self {
			Counter::All => "all".to_string(),
			Counter::Any => "any".to_string(),
			Counter::Number(0) => "zero".to_string(),
			Counter::Number(1) => "one".to_string(),
			Counter::Number(2) => "two".to_string(),
			Counter::Number(3) => "three".to_string(),
			Counter::Number(4) => "four".to_string(),
			Counter::Number(5) => "five".to_string(),
			Counter::Number(6) => "six".to_string(),
			Counter::Number(7) => "seven".to_string(),
			Counter::Number(8) => "eight".to_string(),
			Counter::Number(9) => "nine".to_string(),
			Counter::Number(10) => "ten".to_string(),
			Counter::Number(n) => format!("{}", n),
		}
	}
}

impl fmt::Display for Counter {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		let what: String = match &self {
			Counter::All => "all".to_string(),
			Counter::Any => "any".to_string(),
			Counter::Number(n) => format!("{}", n),
		};
		fmt.write_str(&what)
	}
}

impl Serialize for Counter {
	fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
	where
		S: Serializer,
	{
		match &self {
			Counter::All => serializer.serialize_str("all"),
			Counter::Any => serializer.serialize_str("any"),
			Counter::Number(n) => serializer.serialize_u64(*n),
		}
	}
}

impl<'de> Deserialize<'de> for Counter {
	fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
	where
		D: Deserializer<'de>,
	{
		struct CountVisitor;

		impl<'de> Visitor<'de> for CountVisitor {
			type Value = Counter;

			fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
				f.write_str("`count` as a number, any, or all")
			}

			fn visit_i64<E>(self, num: i64) -> Result<Self::Value, E>
			where
				E: de::Error,
			{
				Err(E::custom(format!("negative numbers are not allowed; was `{}`", num)))
			}

			fn visit_u64<E>(self, num: u64) -> Result<Self::Value, E>
			where
				E: de::Error,
			{
				Ok(Counter::Number(num))
			}

			fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
			where
				E: de::Error,
			{
				match value {
					"all" => Ok(Counter::All),
					"any" => Ok(Counter::Any),
					_ => Err(E::custom(format!("string must be `any` or `all`; was `{}`", value))),
				}
			}
		}

		deserializer.deserialize_any(CountVisitor)
	}
}
