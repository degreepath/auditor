use crate::traits::Util;
use crate::util;

#[cfg(test)]
mod tests;

mod print;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub requirement: String,
	#[serde(default = "util::serde_false")]
	pub optional: bool,
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		false
	}
}
