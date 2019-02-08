use super::{RuleInput, RuleResult};

pub trait Audit {
	fn check(&self, input: &RuleInput) -> RuleResult;
}
