use super::TaggedValue;
use crate::traits::print;
use crate::util::{self, Oxford};
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum WrappedValue<T> {
	Single(TaggedValue<T>),
	Or(Vec<TaggedValue<T>>),
	And(Vec<TaggedValue<T>>),
}

impl WrappedValue<String> {
	pub fn new(s: &str) -> Self {
		WrappedValue::Single(TaggedValue::EqualTo(s.to_string()))
	}
}

impl<T: FromStr> FromStr for WrappedValue<T> {
	type Err = util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		let parts: Vec<_> = s.split(" | ").collect();
		if parts.len() > 1 {
			let mut tagged = Vec::with_capacity(parts.len());

			for part in parts {
				tagged.push(part.parse::<TaggedValue<T>>()?);
			}

			return Ok(WrappedValue::Or(tagged));
		}

		let parts: Vec<_> = s.split(" & ").collect();
		if parts.len() > 1 {
			let mut tagged = Vec::with_capacity(parts.len());

			for part in parts {
				tagged.push(part.parse::<TaggedValue<T>>()?);
			}

			return Ok(WrappedValue::And(tagged));
		}

		Ok(WrappedValue::Single(s.parse::<TaggedValue<T>>()?))
	}
}

impl<T: print::Print> print::Print for WrappedValue<T> {
	fn print(&self) -> print::Result {
		use WrappedValue::{And, Or, Single};

		match &self {
			Single(v) => v.print(),
			Or(v) | And(v) => {
				let v: Vec<String> = v.iter().filter_map(|r| r.print().ok()).collect();

				match &self {
					Or(_) => Ok(v.oxford("or")),
					And(_) => Ok(v.oxford("and")),
					_ => panic!("we already checked for Single"),
				}
			}
		}
	}
}

impl<T: fmt::Display> fmt::Display for WrappedValue<T> {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		use WrappedValue::{And, Or, Single};

		let desc = match &self {
			Single(val) => format!("{}", val),
			And(values) => {
				let parts: Vec<_> = values.iter().map(|v| format!("{}", v)).collect();
				parts.join(" & ")
			}
			Or(values) => {
				let parts: Vec<_> = values.iter().map(|v| format!("{}", v)).collect();
				parts.join(" | ")
			}
		};

		fmt.write_str(&desc)
	}
}

impl PartialEq<String> for WrappedValue<String> {
	fn eq(&self, rhs: &String) -> bool {
		match &self {
			WrappedValue::Single(value) => value == rhs,
			WrappedValue::Or(values) => values.iter().any(|v| v == rhs),
			WrappedValue::And(values) => values.iter().all(|v| v == rhs),
		}
	}
}

impl PartialEq<WrappedValue<String>> for String {
	fn eq(&self, other: &WrappedValue<String>) -> bool {
		other == self
	}
}
