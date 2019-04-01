use crate::grade::{option_grade, Grade};
use crate::student::Semester;
use crate::traits::Util;
use serde::Deserialize;
use std::str::FromStr;

mod print;
mod serialize;
#[cfg(test)]
mod tests;

#[derive(Default, Debug, PartialEq, Clone, Deserialize, Hash, Eq)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub course: String,
	#[serde(default, deserialize_with = "option_grade")]
	pub grade: Option<Grade>,
	pub section: Option<String>,
	pub year: Option<u16>,
	pub semester: Option<Semester>,
	pub lab: Option<bool>,
	pub can_match_used: Option<bool>,
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		false
	}
}

impl FromStr for Rule {
	type Err = void::Void;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		Ok(Rule {
			course: String::from(s),
			..Default::default()
		})
	}
}
