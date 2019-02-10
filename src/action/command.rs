use crate::util::ParseError;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

const COUNT: &str = "count";
const SUM: &str = "sum";
const AVERAGE: &str = "average";
const MINIMUM: &str = "minimum";
const MAXIMUM: &str = "maximum";

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
			COUNT => Ok(Command::Count),
			SUM => Ok(Command::Sum),
			AVERAGE => Ok(Command::Average),
			MINIMUM => Ok(Command::Minimum),
			MAXIMUM => Ok(Command::Maximum),
			_ => Err(ParseError::UnknownCommand),
		}
	}
}

impl fmt::Display for Command {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Command::Count => write!(f, "{}", COUNT),
			Command::Sum => write!(f, "{}", SUM),
			Command::Average => write!(f, "{}", AVERAGE),
			Command::Minimum => write!(f, "{}", MINIMUM),
			Command::Maximum => write!(f, "{}", MAXIMUM),
		}
	}
}

impl From<&Command> for String {
	fn from(c: &Command) -> Self {
		match c {
			Command::Count => String::from(COUNT),
			Command::Sum => String::from(SUM),
			Command::Average => String::from(AVERAGE),
			Command::Minimum => String::from(MINIMUM),
			Command::Maximum => String::from(MAXIMUM),
		}
	}
}

impl PartialEq<String> for Command {
	fn eq(&self, rhs: &String) -> bool {
		&String::from(self) == rhs
	}
}

impl PartialEq<Command> for String {
	fn eq(&self, rhs: &Command) -> bool {
		rhs == self
	}
}
