use crate::action::Operator;
use crate::traits::print;
use crate::util;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum TaggedValue<T> {
	LessThan(T),
	LessThanEqualTo(T),
	EqualTo(T),
	GreaterThan(T),
	GreaterThanEqualTo(T),
	NotEqualTo(T),
}

impl<T> TaggedValue<T> {
	pub fn into_inner(&self) -> &T {
		use TaggedValue::*;
		match &self {
			LessThan(v) | LessThanEqualTo(v) | EqualTo(v) | GreaterThan(v) | GreaterThanEqualTo(v) | NotEqualTo(v) => v,
		}
	}
}

impl TaggedValue<String> {
	pub fn eq_string(s: &str) -> Self {
		TaggedValue::EqualTo(s.to_string())
	}
}

impl crate::util::Pluralizable for TaggedValue<u64> {
	fn should_pluralize(&self) -> bool {
		if *self.into_inner() == 1 {
			false
		} else {
			true
		}
	}
}

impl crate::util::Pluralizable for TaggedValue<decorum::R32> {
	fn should_pluralize(&self) -> bool {
		true
	}
}

impl<T: FromStr> FromStr for TaggedValue<T> {
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
					[op, value] => {
						let op = op.parse::<Operator>()?;
						let value = match value.parse::<T>() {
							Ok(v) => v,
							Err(_) => return Err(util::ParseError::InvalidValue),
						};

						Ok(match op {
							Operator::EqualTo => TaggedValue::EqualTo(value),
							Operator::LessThan => TaggedValue::LessThan(value),
							Operator::LessThanEqualTo => TaggedValue::LessThanEqualTo(value),
							Operator::GreaterThan => TaggedValue::GreaterThan(value),
							Operator::GreaterThanEqualTo => TaggedValue::GreaterThanEqualTo(value),
							Operator::NotEqualTo => TaggedValue::NotEqualTo(value),
						})
					}
					[_] | _ => {
						// println!("{:?}", splitted);
						Err(util::ParseError::InvalidAction)
					}
				}
			}
			_ => {
				if let Ok(v) = s.parse::<T>() {
					Ok(TaggedValue::EqualTo(v))
				} else {
					Err(util::ParseError::InvalidAction)
				}
			}
		}
	}
}

impl print::Print for String {
	fn print(&self) -> print::Result {
		Ok(self.to_string())
	}
}

impl print::Print for decorum::R32 {
	fn print(&self) -> print::Result {
		if (decorum::R32::from(0.0) < *self) && (*self < decorum::R32::from(10.0)) {
			Ok(format!("{:>0.2}", self))
		} else {
			Ok(format!("{}", self))
		}
	}
}

impl print::Print for u64 {
	fn print(&self) -> print::Result {
		Ok(match &self {
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
			_ => self.to_string(),
		})
	}
}

impl<T: print::Print> print::Print for TaggedValue<T> {
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

impl<T: fmt::Display> fmt::Display for TaggedValue<T> {
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

impl PartialEq<String> for TaggedValue<String> {
	fn eq(&self, rhs: &String) -> bool {
		match &self {
			TaggedValue::EqualTo(value) => value == rhs,
			TaggedValue::NotEqualTo(value) => value != rhs,
			_ => unimplemented!(),
		}
	}
}

impl PartialEq<TaggedValue<String>> for String {
	fn eq(&self, other: &TaggedValue<String>) -> bool {
		other == self
	}
}
