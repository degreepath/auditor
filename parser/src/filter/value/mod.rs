use crate::traits::print;
use crate::util;
use std::fmt;
use std::str::FromStr;

mod constant;
mod tagged;
mod wrapped;

pub use constant::Constant;
pub use tagged::TaggedValue;
pub use wrapped::WrappedValue;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Value {
	Constant(Constant),
	Bool(bool),
	Integer(u64),
	Float((u16, u16)),
	String(String),
}

impl print::Print for Value {
	fn print(&self) -> print::Result {
		match &self {
			Value::String(s) => Ok(s.to_string()),
			Value::Integer(n) => Ok(format!("{}", n)),
			Value::Float((i, f)) => Ok(format!("{}.{}", i, f)),
			Value::Bool(b) => Ok(format!("{}", b)),
			Value::Constant(s) => Ok(format!("{}", s)),
		}
	}
}

impl From<String> for Value {
	fn from(s: String) -> Value {
		Value::String(s)
	}
}

impl From<&str> for Value {
	fn from(s: &str) -> Value {
		Value::String(s.to_string())
	}
}

impl From<u64> for Value {
	fn from(i: u64) -> Value {
		Value::Integer(i)
	}
}

impl From<bool> for Value {
	fn from(b: bool) -> Value {
		Value::Bool(b)
	}
}

impl FromStr for Value {
	type Err = util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		if let Ok(constant) = s.parse::<Constant>() {
			return Ok(Value::Constant(constant));
		}

		if let Ok(num) = s.parse::<u64>() {
			return Ok(Value::Integer(num));
		}

		if let Ok(num) = s.parse::<f32>() {
			return Ok(Value::Float((num.trunc() as u16, (num.fract() * 100.0) as u16)));
		}

		if let Ok(b) = s.parse::<bool>() {
			return Ok(Value::Bool(b));
		}

		Ok(Value::String(s.to_string()))
	}
}

impl PartialEq<bool> for Value {
	fn eq(&self, rhs: &bool) -> bool {
		match &self {
			Value::Bool(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<String> for Value {
	fn eq(&self, rhs: &String) -> bool {
		match &self {
			Value::String(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<str> for Value {
	fn eq(&self, rhs: &str) -> bool {
		match &self {
			Value::String(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<u64> for Value {
	fn eq(&self, rhs: &u64) -> bool {
		match &self {
			Value::Integer(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl PartialEq<(u16, u16)> for Value {
	fn eq(&self, rhs: &(u16, u16)) -> bool {
		match &self {
			Value::Float(lhs) => lhs == rhs,
			_ => false,
		}
	}
}

impl fmt::Display for Value {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		let desc = match &self {
			Value::String(s) => s.to_string(),
			Value::Integer(n) => format!("{}", n),
			Value::Float((i, f)) => format!("{}.{:>02}", i, f),
			Value::Bool(b) => format!("{}", b),
			Value::Constant(s) => format!("{}", s),
		};
		fmt.write_str(&desc)
	}
}
