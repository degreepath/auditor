use super::*;
use crate::rules::Rule as AnyRule;
use crate::traits::audit::{
	rule::{Audit, RuleState},
	AuditState,
};

impl Audit for Rule {
	fn check(&self, state: &AuditState) -> RuleState {
		let first = self.either.0.check(state);
		if first.is_pass() {
			return RuleState::pass(AnyRule::Either(self.clone()));
		}

		let second = self.either.1.check(state);
		if second.is_pass() {
			return RuleState::pass(AnyRule::Either(self.clone()));
		}

		RuleState::fail(AnyRule::Either(self.clone()))
	}
}
