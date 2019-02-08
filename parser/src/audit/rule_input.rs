use super::{ReservedPairings, RuleResult, Transcript};
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct RuleInput {
	pub transcript: Transcript,
	pub already_used: ReservedPairings,
	pub completed_siblings: HashMap<String, RuleResult>,
}

impl RuleInput {
	pub fn update(&self, from_result: RuleResult) -> Self {
		RuleInput {
			already_used: self.already_used.union(&from_result.reservations),
			transcript: self.transcript.clone(),
			completed_siblings: self.completed_siblings.clone(),
		}
	}
}
