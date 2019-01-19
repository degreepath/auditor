use crate::rules::Rule as AnyRule;
use crate::surplus::Surplus;
use crate::traits::Util;

mod print;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub both: (Box<AnyRule>, Box<AnyRule>),
	#[serde(default)]
	pub surplus: Option<Surplus>,
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		self.both.0.has_save_rule() || self.both.1.has_save_rule()
	}
}
