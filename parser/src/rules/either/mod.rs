use crate::rules::traits::RuleTools;
use crate::rules::Rule as AnyRule;
use crate::surplus::Surplus;

#[cfg(test)]
mod tests;

mod print;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub either: (Box<AnyRule>, Box<AnyRule>),
	#[serde(default)]
	pub surplus: Option<Surplus>,
}

impl RuleTools for Rule {
	fn has_save_rule(&self) -> bool {
		self.either.0.has_save_rule() || self.either.1.has_save_rule()
	}
}
