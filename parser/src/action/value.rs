use super::Command;
use crate::traits::print;
use crate::util::ParseError;
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Value {
	Command(Command),
	String(String),
	Integer(u64),
	Float((u16, u16)),
}

impl FromStr for Value {
	type Err = ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		if let Ok(num) = s.parse::<u64>() {
			return Ok(Value::Integer(num));
		}

		if let Ok(num) = s.parse::<f32>() {
			return Ok(Value::Float((num.trunc() as u16, (num.fract() * 100.0) as u16)));
		}

		if let Ok(command) = s.parse::<Command>() {
			return Ok(Value::Command(command));
		}

		Ok(Value::String(s.to_string()))
	}
}

impl fmt::Display for Value {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Value::Command(cmd) => write!(f, "{}", cmd),
			Value::String(v) => write!(f, "{}", v),
			Value::Integer(v) => write!(f, "{}", v),
			Value::Float((i, r)) => write!(f, "{}.{:>02}", i, r),
		}
	}
}

impl print::Print for Value {
	fn print(&self) -> print::Result {
		match &self {
			Value::Command(_) => unimplemented!("pretty-printing a Value::Command"),
			Value::String(v) => Ok(format!("“{}”", v)),
			Value::Integer(n) => Ok(match n {
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
			Value::Float((i, r)) => Ok(format!("{}.{:>02}", i, r)),
		}
	}
}
