use crate::util;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

const GRADUATION_YEAR: &str = "$graduation-year";
const SENIOR_YEAR: &str = "$senior-year";
const JUNIOR_YEAR: &str = "$junior-year";

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord, Hash)]
pub enum Constant {
	#[serde(rename = "$graduation-year")]
	GraduationYear,
	#[serde(rename = "$senior-year")]
	SeniorYear,
	#[serde(rename = "$junior-year")]
	JuniorYear,
}

impl fmt::Display for Constant {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Constant::GraduationYear => write!(f, "{}", GRADUATION_YEAR),
			Constant::SeniorYear => write!(f, "{}", SENIOR_YEAR),
			Constant::JuniorYear => write!(f, "{}", JUNIOR_YEAR),
		}
	}
}

impl FromStr for Constant {
	type Err = util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		let s = s.trim();

		match s {
			GRADUATION_YEAR => Ok(Constant::GraduationYear),
			SENIOR_YEAR => Ok(Constant::SeniorYear),
			JUNIOR_YEAR => Ok(Constant::JuniorYear),
			_ => Err(util::ParseError::UnknownCommand),
		}
	}
}

impl<'a> From<&Constant> for String {
	fn from(c: &Constant) -> Self {
		match c {
			Constant::GraduationYear => String::from(GRADUATION_YEAR),
			Constant::SeniorYear => String::from(SENIOR_YEAR),
			Constant::JuniorYear => String::from(JUNIOR_YEAR),
		}
	}
}

impl PartialEq<String> for Constant {
	fn eq(&self, rhs: &String) -> bool {
		&String::from(self) == rhs
	}
}

impl PartialEq<Constant> for String {
	fn eq(&self, rhs: &Constant) -> bool {
		rhs == self
	}
}
