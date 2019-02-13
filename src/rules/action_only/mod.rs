use crate::action::LhsValueAction;
use crate::traits::Util;
use crate::util;
use serde::{Deserialize, Serialize};

mod print;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	#[serde(rename = "do")]
	pub action: LhsValueAction,
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		true
	}
}
