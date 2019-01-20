use crate::action::Action;
use crate::traits::Util;
use crate::util;

mod print;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	#[serde(rename = "do", deserialize_with = "util::string_or_struct_parseerror")]
	pub action: Action,
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		true
	}
}
