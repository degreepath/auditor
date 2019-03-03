use crate::traits::Util;
use crate::util;
use serde::{Deserialize, Serialize};

mod audit;
mod print;
#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize, Clone, Hash)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub name: String,
	#[serde(default = "util::serde_false")]
	pub optional: bool,
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		false
	}
}
