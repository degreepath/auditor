use crate::util;
use serde::de::{Deserialize, Deserializer};
use std::fmt;

#[cfg(test)]
mod tests;

mod command;
pub use command::Command;
mod value;
pub use value::Value;
mod operator;
mod parse;
mod print;
pub use operator::Operator;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Action {
	pub lhs: Value,
	pub op: Option<Operator>,
	pub rhs: Option<Value>,
}

// I think this comparison is OK, because we won't ever be _modifying_
// these values; we'll just be comparing them against other values that
// came attached to courses.
const ONE: f64 = 1.0;

impl Action {
	pub fn should_pluralize(&self) -> bool {
		match &self.rhs {
			Some(Value::Integer(n)) if *n == 1 => false,
			Some(Value::Integer(_)) => true,
			Some(Value::Float(f)) if *f == ONE => false,
			Some(Value::Float(_)) => true,
			_ => false,
		}
	}
}

impl fmt::Display for Action {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Action {
				lhs,
				rhs: None,
				op: None,
			} => write!(f, "{}", lhs),
			Action {
				lhs,
				rhs: Some(rhs),
				op: Some(op),
			} => write!(f, "{} {} {}", lhs, op, rhs),
			_ => Err(fmt::Error),
		}
	}
}

pub fn option_action<'de, D>(deserializer: D) -> Result<Option<Action>, D::Error>
where
	D: Deserializer<'de>,
{
	#[derive(Deserialize)]
	struct Wrapper(#[serde(deserialize_with = "util::string_or_struct_parseerror")] Action);

	let v = Option::deserialize(deserializer)?;
	Ok(v.map(|Wrapper(a)| a))
}
