use serde::de::{self, Deserialize, Deserializer, MapAccess, Visitor};
use std::error::Error;
use std::fmt;
use std::marker::PhantomData;
use std::str::FromStr;
use void::Void;

pub trait Oxford {
	fn oxford(&self, trailer: &str) -> String;
}

impl Oxford for Vec<String> {
	fn oxford(&self, trailer: &str) -> String {
		if self.len() == 1 {
			return format!("{}", self[0]);
		}

		if self.len() == 2 {
			return format!("{} {} {}", self[0], trailer, self[1]);
		}

		if let Some((last, rest)) = self.split_last() {
			return format!("{}, {} {}", rest.join(", "), trailer, last);
		}

		String::new()
	}
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
	InvalidAction,
	UnknownOperator,
	InvalidValue,
	UnknownCommand,
	InvalidVariableName,
}

impl fmt::Display for ParseError {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		fmt.write_str(self.description())
	}
}

impl Error for ParseError {
	fn description(&self) -> &str {
		"invalid do: command syntax"
	}
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ValidationError {
	GivenAreasMustOutputAreas,
}

impl fmt::Display for ValidationError {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		fmt.write_str(self.description())
	}
}

impl Error for ValidationError {
	fn description(&self) -> &str {
		match &self {
			ValidationError::GivenAreasMustOutputAreas => {
				"in a `given: areas of study` block, `what:` must also be `areas of study`"
			}
		}
	}
}

pub fn pretty_term(term: &str) -> String {
	format!("{}", term)
}

pub fn expand_year(year: u64, mode: &str) -> String {
	match mode {
		"short" => format!("{}", year),
		"dual" => {
			let next = year + 1;
			let next = next.to_string();
			let next = &next[2..4];
			format!("{}-{}", year, next)
		}
		_ => panic!("unknown expand_year mode {}", mode),
	}
}

pub fn serde_false() -> bool {
	false
}

pub fn string_or_struct<'de, T, D>(deserializer: D) -> Result<T, D::Error>
where
	T: Deserialize<'de> + FromStr<Err = Void>,
	D: Deserializer<'de>,
{
	// This is a Visitor that forwards string types to T's `FromStr` impl and
	// forwards map types to T's `Deserialize` impl. The `PhantomData` is to
	// keep the compiler from complaining about T being an unused generic type
	// parameter. We need T in order to know the Value type for the Visitor
	// impl.
	struct StringOrStruct<T>(PhantomData<fn() -> T>);

	impl<'de, T> Visitor<'de> for StringOrStruct<T>
	where
		T: Deserialize<'de> + FromStr<Err = Void>,
	{
		type Value = T;

		fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
			formatter.write_str("string or map")
		}

		fn visit_str<E>(self, value: &str) -> Result<T, E>
		where
			E: de::Error,
		{
			Ok(FromStr::from_str(value).unwrap())
		}

		fn visit_map<M>(self, visitor: M) -> Result<T, M::Error>
		where
			M: MapAccess<'de>,
		{
			// `MapAccessDeserializer` is a wrapper that turns a `MapAccess`
			// into a `Deserializer`, allowing it to be used as the input to T's
			// `Deserialize` implementation. T then deserializes itself using
			// the entries from the map visitor.
			Deserialize::deserialize(de::value::MapAccessDeserializer::new(visitor))
		}
	}

	deserializer.deserialize_any(StringOrStruct(PhantomData))
}

pub fn string_or_struct_parseerror<'de, T, D>(deserializer: D) -> Result<T, D::Error>
where
	T: Deserialize<'de> + FromStr<Err = ParseError>,
	D: Deserializer<'de>,
{
	// This is a Visitor that forwards string types to T's `FromStr` impl and
	// forwards map types to T's `Deserialize` impl. The `PhantomData` is to
	// keep the compiler from complaining about T being an unused generic type
	// parameter. We need T in order to know the Value type for the Visitor
	// impl.
	struct StringOrStruct<T>(PhantomData<fn() -> T>);

	impl<'de, T> Visitor<'de> for StringOrStruct<T>
	where
		T: Deserialize<'de> + FromStr<Err = ParseError>,
	{
		type Value = T;

		fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
			formatter.write_str("string or map")
		}

		fn visit_str<E>(self, value: &str) -> Result<T, E>
		where
			E: de::Error,
		{
			Ok(FromStr::from_str(value).unwrap())
		}

		fn visit_map<M>(self, visitor: M) -> Result<T, M::Error>
		where
			M: MapAccess<'de>,
		{
			// `MapAccessDeserializer` is a wrapper that turns a `MapAccess`
			// into a `Deserializer`, allowing it to be used as the input to T's
			// `Deserialize` implementation. T then deserializes itself using
			// the entries from the map visitor.
			Deserialize::deserialize(de::value::MapAccessDeserializer::new(visitor))
		}
	}

	deserializer.deserialize_any(StringOrStruct(PhantomData))
}

#[cfg(test)]
mod tests {
	#[test]
	fn oxford_len_eq0() {
		use super::Oxford;
		assert_eq!("", vec![].oxford("and"));
	}

	#[test]
	fn oxford_len_eq1() {
		use super::Oxford;
		assert_eq!("A", vec!["A".to_string()].oxford("and"));
	}

	#[test]
	fn oxford_len_eq2() {
		use super::Oxford;
		assert_eq!("A and B", vec!["A".to_string(), "B".to_string()].oxford("and"));
		assert_eq!("A or B", vec!["A".to_string(), "B".to_string()].oxford("or"));
	}

	#[test]
	fn oxford_len_gt3() {
		use super::Oxford;
		assert_eq!(
			"A, B, and C",
			vec!["A".to_string(), "B".to_string(), "C".to_string()].oxford("and")
		);
		assert_eq!(
			"A, B, or C",
			vec!["A".to_string(), "B".to_string(), "C".to_string()].oxford("or")
		);
	}
}
