use crate::util;
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Eq, PartialOrd, Ord, Hash)]
pub enum Constant {
	#[serde(rename = "graduation-year")]
	GraduationYear,
}

impl fmt::Display for Constant {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Constant::GraduationYear => write!(f, "graduation-year"),
		}
	}
}

impl FromStr for Constant {
	type Err = util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		let s = s.trim();

		match s {
			"graduation-year" => Ok(Constant::GraduationYear),
			_ => Err(util::ParseError::UnknownCommand),
		}
	}
}
