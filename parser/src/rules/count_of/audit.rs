use super::Counter;
use crate::audit::{ReservedPairings, RuleAudit, RuleInput, RuleResult, RuleResultDetails, RuleStatus};
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

		let mut successes = 0;
		let mut results = Vec::with_capacity(count);

		let mut input: RuleInput = input.clone();
		for rule in self.of.iter() {
			let result = rule.check(&input);

			results.push(Some(result.clone()));

			if result.is_pass() {
				successes += 1;
			}

			if successes == count {
				break;
			}

			input = input.update(result);
		}

		for _ in successes..count {
			results.push(None);
		}

		assert_eq!(results.len(), count);

		if successes != count {
			return RuleResult::fail(&RuleResultDetails::CountOf(results));
		}

		let reservations = results
			.iter()
			.filter_map(|item| item.as_ref())
			.fold(ReservedPairings::new(), |acc, r| acc.union(&r.reservations));

		RuleResult {
			detail: RuleResultDetails::CountOf(results),
			reservations,
			status: RuleStatus::Pass,
		}
	}
}
