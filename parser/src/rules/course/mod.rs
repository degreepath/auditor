use crate::traits::Util;
use std::str::FromStr;
use void::Void;

mod audit;
mod print;
mod serialize;

#[cfg(test)]
mod tests;

#[derive(Default, Debug, PartialEq, Clone, Deserialize, Hash, Eq)]
pub struct Rule {
	pub course: String,
	pub term: Option<String>,
	pub section: Option<String>,
	pub year: Option<u64>,
	pub semester: Option<String>,
	pub lab: Option<bool>,
	pub can_match_used: Option<bool>,
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		false
	}
}

impl FromStr for Rule {
	// This implementation of `from_str` can never fail, so use the impossible
	// `Void` type as the error type.
	type Err = Void;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		Ok(Rule {
			course: String::from(s),
			..Default::default()
		})
	}
}
