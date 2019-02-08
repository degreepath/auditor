use crate::audit::{RuleAudit, RuleInput, RuleResult, RuleResultDetails, RuleStatus};
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
			return RuleResult {
				detail: RuleResultDetails::Either((Some(Box::new(a.clone())), None)),
				reservations: a.reservations.clone(),
				status: RuleStatus::Pass,
			};
		}

		let b = self.either.1.check(input);
		if b.is_pass() {
			return RuleResult {
				detail: RuleResultDetails::Either((None, Some(Box::new(b.clone())))),
				reservations: b.reservations.clone(),
				status: RuleStatus::Pass,
			};
		}

		RuleResult::fail(&RuleResultDetails::Either((None, None)))
	}
}
