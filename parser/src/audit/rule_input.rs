use super::{ReservedPairings, RuleResult, Transcript};
use std::collections::HashMap;

pub struct RuleInput {
	pub transcript: Transcript,
	pub already_used: ReservedPairings,
	pub completed_siblings: HashMap<String, RuleResult>,
}
