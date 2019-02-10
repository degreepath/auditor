use crate::util::ParseError;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord)]
pub enum Command {
	Count,
	Sum,
	Average,
	Minimum,
	Maximum,
}

impl FromStr for Command {
	type Err = ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		let s = s.trim();

		match s {
			"count" => Ok(Command::Count),
			"sum" => Ok(Command::Sum),
			"average" => Ok(Command::Average),
			"minimum" => Ok(Command::Minimum),
			"maximum" => Ok(Command::Maximum),
			_ => Err(ParseError::UnknownCommand),
		}
	}
}

impl fmt::Display for Command {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Command::Count => write!(f, "count"),
			Command::Sum => write!(f, "sum"),
			Command::Average => write!(f, "average"),
			Command::Minimum => write!(f, "minimum"),
			Command::Maximum => write!(f, "maximum"),
		}
	}
}
