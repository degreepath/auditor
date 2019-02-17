use super::{ReservedPairings, RuleResult};
use crate::student::StudentData;
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct RuleInput {
	pub data: StudentData,
	pub already_used: ReservedPairings,
	pub completed_siblings: HashMap<String, RuleResult>,
}

impl RuleInput {
	pub fn update(&self, from_result: RuleResult) -> Self {
		RuleInput {
			already_used: self.already_used.union(&from_result.reservations),
			data: self.data.clone(),
			completed_siblings: self.completed_siblings.clone(),
		}
	}
}
