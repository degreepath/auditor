use crate::audit::{RuleInput, RuleResult, RuleStatus};

impl super::Rule {
	pub fn to_rule(&self) -> crate::rules::Rule {
		crate::rules::Rule::Course(self.clone())
	}
}

impl super::Rule {
	pub fn check(&self, input: &RuleInput) -> RuleResult {
		if let Some((course, matched_by_what)) = input.transcript.has_course_matching(self, input.already_used.clone())
		{
			let mut used = input.already_used.clone();
			used.add(&(course, self.clone(), matched_by_what));

			RuleResult {
				rule: self.to_rule(),
				reservations: used,
				status: RuleStatus::Pass,
			}
		} else {
			RuleResult::fail(self.to_rule())
		}
	}
}
