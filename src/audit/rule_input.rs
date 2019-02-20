use super::{ReservedPairings, RuleResult};
use crate::save::SaveBlock;
use crate::student::StudentData;
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct RuleInput {
	pub data: StudentData,
	pub used_courses: ReservedPairings,
	pub preceding_requirements: HashMap<String, RuleResult>,
	pub saves: HashMap<String, SaveBlock>,
}

impl RuleInput {
	pub fn update(&self, from_result: RuleResult) -> Self {
		RuleInput {
			used_courses: self.used_courses.union(&from_result.reservations),
			..self.clone()
		}
	}
}
