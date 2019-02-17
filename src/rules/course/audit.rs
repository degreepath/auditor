use crate::audit::{RuleAudit, RuleInput, RuleResult, RuleResultDetails, RuleStatus};

impl super::Rule {
	pub fn to_rule(&self) -> crate::rules::Rule {
		crate::rules::Rule::Course(self.clone())
	}
}

impl RuleAudit for super::Rule {
	fn check(&self, input: &RuleInput) -> RuleResult {
		let transcript = &input.data.transcript;
		let already_used = &input.already_used;

		match transcript.has_course_matching(self, already_used.clone()) {
			Some((course, matched_by_what)) => {
				let mut used = already_used.clone();
				used.add(&(course, matched_by_what));

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
	use crate::audit::{ReservedPairings, RuleAudit, RuleInput, Transcript};
	use crate::filterable_data::{DataValue, FilterableData};
	use crate::student::{CourseInstance, StudentData};
	use maplit::btreemap;
	use std::collections::HashMap;

	#[test]
	fn basic() {
		let rule = CourseRule {
			course: "AMCON 101".to_string(),
			..Default::default()
		};

		let input = RuleInput {
			data: StudentData {
				transcript: Transcript::new(&[CourseInstance::new(FilterableData::new(btreemap! {
					"course".into() => DataValue::String("AMCON 101".to_string()),
				}))]),
				areas: vec![],
				attendances: vec![],
				organizations: vec![],
				performances: vec![],
				overrides: vec![],
			},
			already_used: ReservedPairings::new(),
			completed_siblings: HashMap::new(),
		};

		let result = rule.check(&input);

		assert!(result.is_pass())
	}
}
