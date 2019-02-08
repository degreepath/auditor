use crate::audit::{RuleAudit, RuleInput, RuleResult, RuleResultDetails, RuleStatus};
use crate::rules::Rule as AnyRule;

impl super::Rule {
	pub fn to_rule(&self) -> AnyRule {
		AnyRule::Both(self.clone())
	}
}

impl RuleAudit for super::Rule {
	fn check(&self, input: &RuleInput) -> RuleResult {
		let a = self.both.0.check(input);

		let input = input.update(a.clone());

		let b = self.both.1.check(&input);

		if a.is_pass() && b.is_pass() {
			return RuleResult {
				detail: RuleResultDetails::Both((Box::new(a.clone()), Box::new(b.clone()))),
				reservations: a.reservations.union(&b.reservations),
				status: RuleStatus::Pass,
			};
		}

		RuleResult::fail(&RuleResultDetails::Both((Box::new(a), Box::new(b))))
	}
}
