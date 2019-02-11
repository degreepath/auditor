mod command;
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

// trait ActionsForSlice<T> {
// 	fn count(&self) -> usize;
// 	fn sum(&self) -> T;
// 	fn average(&self) -> f32;
// 	fn maximum(&self) -> Option<&T>;
// 	fn minimum(&self) -> Option<&T>;
// }

// impl<T> ActionsForSlice<T> for &[u64] {
// 	fn count(&self) -> usize {
// 		self.len()
// 	}

// 	fn sum(&self) -> u64 {
// 		self.iter().sum()
// 	}

// 	fn average(&self) -> f32 {
// 		self.sum() / self.count()
// 	}

// 	fn maximum(&self) -> Option<&u64> {
// 		self.iter().max()
// 	}

// 	fn minimum(&self) -> Option<&u64> {
// 		self.iter().min()
// 	}
// }

// impl<T> ActionsForSlice<T> for &[f32] {
// 	fn count(&self) -> usize {
// 		self.len()
// 	}

// 	fn sum(&self) -> f32 {
// 		self.iter().sum()
// 	}

// 	fn average(&self) -> f32 {
// 		self.sum() / self.count()
// 	}

// 	fn maximum(&self) -> Option<&f32> {
// 		if self.is_empty() {
// 			return None;
// 		}

// 		let mut biggest = &self[0];
// 		for item in self.iter() {
// 			biggest = &item.max(*biggest);
// 		}

// 		Some(biggest)
// 	}

// 	fn minimum(&self) -> Option<&f32> {
// 		if self.is_empty() {
// 			return None;
// 		}

// 		let mut smallest = &self[0];
// 		for item in self.iter() {
// 			smallest = &item.min(*smallest);
// 		}

// 		Some(smallest)
// 	}
// }

impl Action {
	pub fn compute<T>(&self, data: &[T]) -> bool
	where
		T: Ord + PartialEq<Value> + PartialOrd<Value>,
	{
		if self.rhs.is_none() {
			return false;
		}

		let rhs = self.rhs.unwrap();

		match &self.lhs {
			Count => {
				let lhs = data.len() as u64;
				self.cmp(&lhs, &rhs)
			}
			Sum => {
				let lhs = data.iter().sum();
				self.cmp(&lhs, &rhs)
			}
			Average => {
				let lhs = data.iter().sum() / (data.len() as f64);
				self.cmp(&lhs, &rhs)
			}
			Maximum => match data.iter().max() {
				Some(lhs) => self.cmp(&lhs, &rhs),
				None => false,
			},
			Minimum => match data.iter().min() {
				Some(lhs) => self.cmp(&lhs, &rhs),
				None => false,
			},
		}
	}

	fn cmp<T>(self, lhs: &T, rhs: &Value) -> bool
	where
		T: PartialEq<Value> + PartialOrd<Value>,
	{
		match &self.op {
			Some(Operator::EqualTo) => lhs == rhs,
			Some(Operator::NotEqualTo) => lhs != rhs,
			Some(Operator::LessThan) => lhs < rhs,
			Some(Operator::LessThanEqualTo) => lhs <= rhs,
			Some(Operator::GreaterThan) => lhs > rhs,
			Some(Operator::GreaterThanEqualTo) => lhs >= rhs,
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
