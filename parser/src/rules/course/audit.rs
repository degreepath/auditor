use super::*;
use crate::rules::Rule as AnyRule;
use crate::traits::audit::{
	rule::{Audit, RuleState},
	AuditState,
};

impl Audit for Rule {
	fn check(&self, state: &AuditState) -> RuleState {
		if state.has_course_matching(&self) {
			RuleState::pass(AnyRule::Course(self.clone()))
		} else {
			RuleState::fail(AnyRule::Course(self.clone()))
		}
	}
}
