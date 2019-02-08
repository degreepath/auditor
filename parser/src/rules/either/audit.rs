use crate::audit::{RuleAudit, RuleInput, RuleResult};
use crate::rules::Rule as AnyRule;

impl super::Rule {
	pub fn to_rule(&self) -> AnyRule {
		AnyRule::Either(self.clone())
	}
}

impl RuleAudit for super::Rule {
	fn check(&self, input: &RuleInput) -> RuleResult {
		let a = self.either.0.check(input);
		if a.is_pass() {
			return a;
		}

		let b = self.either.1.check(input);
		if b.is_pass() {
			return b;
		}

		RuleResult::fail(self.to_rule())
	}
}
