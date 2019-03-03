use crate::action::Operator;
use crate::traits::print;
use crate::util;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord, Hash)]
pub enum TaggedValue<T> {
	LessThan(T),
	LessThanEqualTo(T),
	EqualTo(T),
	GreaterThan(T),
	GreaterThanEqualTo(T),
	NotEqualTo(T),
}

impl TaggedValue<String> {
	pub fn eq_string(s: &str) -> Self {
		TaggedValue::EqualTo(s.to_string())
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
		Ok(self.to_string())
	}
}

impl print::Print for u64 {
	fn print(&self) -> print::Result {
		Ok(self.to_string())
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
