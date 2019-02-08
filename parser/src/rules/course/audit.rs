use crate::audit::{RuleAudit, RuleInput, RuleResult, RuleResultDetails, RuleStatus};

impl super::Rule {
	pub fn to_rule(&self) -> crate::rules::Rule {
		crate::rules::Rule::Course(self.clone())
	}
}

impl RuleAudit for super::Rule {
	fn check(&self, input: &RuleInput) -> RuleResult {
		let transcript = &input.transcript;
		let already_used = &input.already_used;

		match transcript.has_course_matching(self, already_used.clone()) {
			Some((course, matched_by_what)) => {
				let mut used = already_used.clone();
				used.add(&(course, self.clone(), matched_by_what));

				RuleResult {
					detail: RuleResultDetails::Course,
					reservations: used,
					status: RuleStatus::Pass,
				}
			}
			None => RuleResult::fail(&RuleResultDetails::Course),
		}
	}
}
