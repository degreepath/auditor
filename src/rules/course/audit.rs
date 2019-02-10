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

#[cfg(test)]
mod tests {
	use super::super::Rule as CourseRule;
	use crate::audit::{CourseInstance, ReservedPairings, RuleAudit, RuleInput, Transcript};
	use std::collections::HashMap;

	#[test]
	fn basic() {
		let rule = CourseRule {
			course: "AMCON 101".to_string(),
			..Default::default()
		};

		let input = RuleInput {
			transcript: Transcript::new(&[CourseInstance {
				attributes: vec![],
				course_type: "Instruction".to_string(),
				course: "AMCON 101".to_string(),
				gereqs: vec![],
				section: None,
				semester: "Fall".to_string(),
				subjects: vec!["AMCON".to_string()],
				term: "2018-1".to_string(),
				year: 2018,
			}]),
			already_used: ReservedPairings::new(),
			completed_siblings: HashMap::new(),
		};

		let result = rule.check(&input);

		assert!(result.is_pass())
	}
}
