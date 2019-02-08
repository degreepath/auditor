use super::Counter;
use crate::audit::{ReservedPairings, RuleAudit, RuleInput, RuleResult, RuleStatus};
use crate::rules::Rule as AnyRule;

impl super::Rule {
	pub fn to_rule(&self) -> AnyRule {
		AnyRule::CountOf(self.clone())
	}
}

impl RuleAudit for super::Rule {
	fn check(&self, input: &RuleInput) -> RuleResult {
		let count: usize = match self.count {
			Counter::All => self.of.len(),
			Counter::Any => 1,
			Counter::Number(n) => n as usize,
		};

		let mut successes = Vec::with_capacity(count);

		let mut input: RuleInput = input.clone();
		for rule in self.of.iter() {
			let result = rule.check(&input);

			if result.is_pass() {
				successes.push(result.clone());
			}

			if successes.len() == count {
				break;
			}

			input = input.update(result);
		}

		if successes.len() != count {
			return RuleResult::fail(self.to_rule());
		}

		RuleResult {
			rule: self.to_rule(),
			reservations: successes
				.iter()
				.fold(ReservedPairings::new(), |acc, r| acc.union(&r.reservations)),
			status: RuleStatus::Pass,
		}
	}
}
