use crate::audit::{RequirementResult, RuleAudit, RuleInput, RuleResult, RuleResultDetails, RuleStatus};
use crate::rules::Rule as AnyRule;

impl super::Rule {
	pub fn to_rule(&self) -> AnyRule {
		AnyRule::Requirement(self.clone())
	}
}

#[allow(clippy::match_bool)]
impl RuleAudit for super::Rule {
	fn check(&self, input: &RuleInput) -> RuleResult {
		match input.preceding_requirements.get(&self.requirement) {
			Some(reference) => match reference.status {
				RuleStatus::Pass => RuleResult {
					detail: RuleResultDetails::Requirement(RequirementResult {}),
					reservations: reference.reservations.clone(),
					status: RuleStatus::Pass,
				},
				RuleStatus::Fail => RuleResult {
					detail: RuleResultDetails::Requirement(RequirementResult {}),
					reservations: reference.reservations.clone(),
					status: RuleStatus::Fail,
				},
				RuleStatus::Skipped => unimplemented!(),
				RuleStatus::Pending => unimplemented!(),
			},
			None => match self.optional {
				true => RuleResult::skip(&RuleResultDetails::Requirement(RequirementResult {})),
				false => RuleResult::fail(&RuleResultDetails::Requirement(RequirementResult {})),
			},
		}
	}
}
