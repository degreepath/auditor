use super::SingleValue;
use crate::action::Operator;
use crate::traits::print;
use crate::util;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord, Hash)]
pub enum TaggedValue {
	LessThan(SingleValue),
	LessThanEqualTo(SingleValue),
	EqualTo(SingleValue),
	GreaterThan(SingleValue),
	GreaterThanEqualTo(SingleValue),
	NotEqualTo(SingleValue),
}

impl TaggedValue {
	// TODO: remove this method
	pub fn is_true(&self) -> bool {
		match &self {
			TaggedValue::EqualTo(v) => *v == true,
			_ => false,
		}
	}

	pub fn eq_string(s: &str) -> Self {
		TaggedValue::EqualTo(SingleValue::String(s.to_string()))
	}
}

impl FromStr for TaggedValue {
	type Err = util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		match s.get(0..1) {
			Some("!") | Some("<") | Some(">") | Some("=") => {
				let splitted: Vec<&str> = s.split_whitespace().collect();

				let splitted = if let Some((first, rest)) = splitted.split_first() {
					vec![first.to_string(), rest.join(" ")]
				} else {
					vec![]
				};

				match splitted.as_slice() {
					[value] => {
						let value = value.parse::<SingleValue>()?;

						Ok(TaggedValue::EqualTo(value))
					}
					[op, value] => {
						let op = op.parse::<Operator>()?;
						let value = value.parse::<SingleValue>()?;

						Ok(match op {
							Operator::EqualTo => TaggedValue::EqualTo(value),
							Operator::LessThan => TaggedValue::LessThan(value),
							Operator::LessThanEqualTo => TaggedValue::LessThanEqualTo(value),
							Operator::GreaterThan => TaggedValue::GreaterThan(value),
							Operator::GreaterThanEqualTo => TaggedValue::GreaterThanEqualTo(value),
							Operator::NotEqualTo => TaggedValue::NotEqualTo(value),
						})

						// Ok(TaggedValue { op, value })
					}
					_ => {
						// println!("{:?}", splitted);
						Err(util::ParseError::InvalidAction)
					}
				}
			}
			_ => {
				let value = s.parse::<SingleValue>()?;

				Ok(TaggedValue::EqualTo(value))
			}
		}
	}
}

impl print::Print for TaggedValue {
	fn print(&self) -> print::Result {
		Ok(match &self {
			TaggedValue::EqualTo(v) => v.print()?,
			TaggedValue::LessThan(v) => format!("fewer than {}", v.print()?),
			TaggedValue::LessThanEqualTo(v) => format!("at most {}", v.print()?),
			TaggedValue::GreaterThan(v) => format!("more than {}", v.print()?),
			TaggedValue::GreaterThanEqualTo(v) => format!("at least {}", v.print()?),
			TaggedValue::NotEqualTo(v) => format!("not {}", v.print()?),
		})
	}
}

impl fmt::Display for TaggedValue {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			TaggedValue::LessThan(v) => write!(fmt, "< {}", v),
			TaggedValue::LessThanEqualTo(v) => write!(fmt, "<= {}", v),
			TaggedValue::EqualTo(v) => write!(fmt, "= {}", v),
			TaggedValue::GreaterThan(v) => write!(fmt, "> {}", v),
			TaggedValue::GreaterThanEqualTo(v) => write!(fmt, ">= {}", v),
			TaggedValue::NotEqualTo(v) => write!(fmt, "! {}", v),
		}
	}
}

impl PartialEq<bool> for TaggedValue {
	fn eq(&self, rhs: &bool) -> bool {
		match &self {
			TaggedValue::EqualTo(value) => value == rhs,
			_ => unimplemented!(),
		}
	}
}

impl PartialEq<String> for TaggedValue {
	fn eq(&self, rhs: &String) -> bool {
		match &self {
			TaggedValue::EqualTo(value) => value == rhs,
			_ => unimplemented!(),
		}
	}
}

impl PartialEq<str> for TaggedValue {
	fn eq(&self, rhs: &str) -> bool {
		match &self {
			TaggedValue::EqualTo(value) => value == rhs,
			_ => unimplemented!(),
		}
	}
}

impl PartialEq<u64> for TaggedValue {
	fn eq(&self, rhs: &u64) -> bool {
		match &self {
			TaggedValue::EqualTo(value) => value == rhs,
			_ => unimplemented!(),
		}
	}
}

impl PartialEq<(u16, u16)> for TaggedValue {
	fn eq(&self, rhs: &(u16, u16)) -> bool {
		match &self {
			TaggedValue::EqualTo(value) => value == rhs,
			_ => unimplemented!(),
		}
	}
}

impl PartialEq<TaggedValue> for bool {
	fn eq(&self, rhs: &TaggedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<TaggedValue> for String {
	fn eq(&self, rhs: &TaggedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<TaggedValue> for str {
	fn eq(&self, rhs: &TaggedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<TaggedValue> for u64 {
	fn eq(&self, rhs: &TaggedValue) -> bool {
		rhs == self
	}
}

impl PartialEq<TaggedValue> for (u16, u16) {
	fn eq(&self, rhs: &TaggedValue) -> bool {
		rhs == self
	}
}
