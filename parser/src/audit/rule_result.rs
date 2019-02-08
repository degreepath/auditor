use super::ReservedPairings;

#[derive(Debug, Clone)]
pub struct RuleResult {
	pub rule: crate::rules::Rule,
	pub reservations: ReservedPairings,
	pub status: RuleStatus,
}

impl RuleResult {
	pub fn pass(rule: crate::rules::Rule) -> RuleResult {
		RuleResult {
			rule: rule.clone(),
			reservations: ReservedPairings::new(),
			status: RuleStatus::Pass,
		}
	}

	pub fn fail(rule: crate::rules::Rule) -> RuleResult {
		RuleResult {
			rule: rule.clone(),
			reservations: ReservedPairings::new(),
			status: RuleStatus::Fail,
		}
	}

	pub fn is_pass(&self) -> bool {
		match self.status {
			RuleStatus::Pass => true,
			_ => false,
		}
	}

	pub fn is_fail(&self) -> bool {
		match self.status {
			RuleStatus::Fail => true,
			_ => false,
		}
	}
}

#[derive(Hash, PartialEq, Eq, Debug, Clone)]
pub enum RuleStatus {
	Pass,
	Fail,
	#[allow(dead_code)]
	Skipped,
	#[allow(dead_code)]
	Pending,
}
