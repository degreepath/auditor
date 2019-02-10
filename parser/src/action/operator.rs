use crate::traits::print;
use crate::util::ParseError;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord, Hash)]
pub enum Operator {
	LessThan,
	LessThanEqualTo,
	EqualTo,
	GreaterThan,
	GreaterThanEqualTo,
	NotEqualTo,
}

impl print::Print for Operator {
	fn print(&self) -> print::Result {
		Ok(match &self {
			Operator::LessThan => "fewer than",
			Operator::LessThanEqualTo => "at most",
			Operator::EqualTo => "exactly",
			Operator::GreaterThan => "more than",
			Operator::GreaterThanEqualTo => "at least",
			Operator::NotEqualTo => "not",
		}
		.to_string())
	}
}

impl FromStr for Operator {
	type Err = ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		match s {
			"<" => Ok(Operator::LessThan),
			"<=" => Ok(Operator::LessThanEqualTo),
			"=" => Ok(Operator::EqualTo),
			">" => Ok(Operator::GreaterThan),
			">=" => Ok(Operator::GreaterThanEqualTo),
			"!" => Ok(Operator::NotEqualTo),
			_ => Err(ParseError::UnknownOperator),
		}
	}
}

impl fmt::Display for Operator {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Operator::LessThan => write!(f, "<"),
			Operator::LessThanEqualTo => write!(f, "<="),
			Operator::EqualTo => write!(f, "="),
			Operator::GreaterThan => write!(f, ">"),
			Operator::GreaterThanEqualTo => write!(f, ">="),
			Operator::NotEqualTo => write!(f, "!"),
		}
	}
}
