mod command;
mod compute;
mod operator;
mod parse;
mod print;
#[cfg(test)]
mod tests;

use crate::util;
pub use crate::value::SingleValue as Value;
pub use command::Command;
pub use operator::Operator;
use serde::de::Deserializer;
use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Action {
	pub lhs: Command,
	pub op: Option<Operator>,
	pub rhs: Option<Value>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct LhsValueAction {
	pub lhs: Value,
	pub op: Option<Operator>,
	pub rhs: Option<Value>,
}

impl Action {
	pub fn should_pluralize(&self) -> bool {
		match &self.rhs {
			Some(Value::Integer(n)) if *n == 1 => false,
			Some(Value::Integer(_)) => true,
			Some(Value::Float((i, f))) if (i, f) == (&1, &0) => false,
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
