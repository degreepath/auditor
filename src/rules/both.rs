use crate::rules::Rule as AnyRule;
use crate::traits::Util;
use serde::{Deserialize, Serialize};

mod audit;
mod print;
#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub both: (Box<AnyRule>, Box<AnyRule>),
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		self.both.0.has_save_rule() || self.both.1.has_save_rule()
	}
}
