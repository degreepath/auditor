use crate::traits::print;
use crate::util;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord, Hash)]
pub enum SingleValue {
	Bool(bool),
	Integer(u64),
	Float((u16, u16)),
	String(String),
}

impl print::Print for SingleValue {
	fn print(&self) -> print::Result {
		match &self {
			SingleValue::String(s) => Ok(s.to_string()),
			SingleValue::Integer(n) => Ok(match n {
				0 => "zero".to_string(),
				1 => "one".to_string(),
				2 => "two".to_string(),
				3 => "three".to_string(),
				4 => "four".to_string(),
				5 => "five".to_string(),
				6 => "six".to_string(),
				7 => "seven".to_string(),
				8 => "eight".to_string(),
				9 => "nine".to_string(),
				10 => "ten".to_string(),
				_ => format!("{}", n),
			}),
			SingleValue::Float((i, f)) => Ok(format!("{}.{:>02}", i, f)),
			SingleValue::Bool(b) => Ok(format!("{}", b)),
		}
	}
}

impl From<String> for SingleValue {
	fn from(s: String) -> SingleValue {
		SingleValue::String(s)
	}
}

impl From<&str> for SingleValue {
	fn from(s: &str) -> SingleValue {
		SingleValue::String(s.to_string())
	}
}

impl From<u64> for SingleValue {
	fn from(i: u64) -> SingleValue {
		SingleValue::Integer(i)
	}
}

impl From<bool> for SingleValue {
	fn from(b: bool) -> SingleValue {
		SingleValue::Bool(b)
	}
}

impl FromStr for SingleValue {
	type Err = util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		if let Ok(num) = s.parse::<u64>() {
			return Ok(SingleValue::Integer(num));
		}

		if let Ok(num) = s.parse::<f32>() {
			return Ok(SingleValue::Float((num.trunc() as u16, (num.fract() * 100.0) as u16)));
		}

		if let Ok(b) = s.parse::<bool>() {
			return Ok(SingleValue::Bool(b));
		}

		Ok(SingleValue::String(s.to_string()))
	}
}

impl PartialEq<bool> for SingleValue {
	fn eq(&self, rhs: &bool) -> bool {
		match &self {
			SingleValue::Bool(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<String> for SingleValue {
	fn eq(&self, rhs: &String) -> bool {
		match &self {
			SingleValue::String(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<str> for SingleValue {
	fn eq(&self, rhs: &str) -> bool {
		match &self {
			SingleValue::String(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<u64> for SingleValue {
	fn eq(&self, rhs: &u64) -> bool {
		match &self {
			SingleValue::Integer(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<(u16, u16)> for SingleValue {
	fn eq(&self, rhs: &(u16, u16)) -> bool {
		match &self {
			SingleValue::Float(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<SingleValue> for bool {
	fn eq(&self, rhs: &SingleValue) -> bool {
		rhs == self
	}
}

impl PartialEq<SingleValue> for String {
	fn eq(&self, rhs: &SingleValue) -> bool {
		rhs == self
	}
}

impl PartialEq<SingleValue> for str {
	fn eq(&self, rhs: &SingleValue) -> bool {
		rhs == self
	}
}

impl PartialEq<SingleValue> for u64 {
	fn eq(&self, rhs: &SingleValue) -> bool {
		rhs == self
	}
}

impl PartialEq<SingleValue> for (u16, u16) {
	fn eq(&self, rhs: &SingleValue) -> bool {
		rhs == self
	}
}

impl fmt::Display for SingleValue {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		let desc = match &self {
			SingleValue::String(s) => s.to_string(),
			SingleValue::Integer(n) => format!("{}", n),
			SingleValue::Float((i, f)) => format!("{}.{:>02}", i, f),
			SingleValue::Bool(b) => format!("{}", b),
		};
		fmt.write_str(&desc)
	}
}

impl std::cmp::PartialOrd<u64> for SingleValue {
	fn partial_cmp(&self, other: &u64) -> Option<std::cmp::Ordering> {
		match self {
			SingleValue::Integer(i) => Some(i.cmp(other)),
			_ => None,
		}
	}
}

impl std::cmp::PartialOrd<SingleValue> for u64 {
	fn partial_cmp(&self, other: &SingleValue) -> Option<std::cmp::Ordering> {
		other.partial_cmp(self)
	}
}
