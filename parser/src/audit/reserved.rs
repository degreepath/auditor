use super::{CourseInstance, MatchedCourseParts};
use crate::rules::course::Rule as CourseRule;
use std::collections::HashSet as Set;

pub type Reservation = (CourseInstance, CourseRule, MatchedCourseParts);

#[derive(Debug, Clone, Default)]
pub struct ReservedPairings(Set<Reservation>);

impl ReservedPairings {
	pub fn new() -> Self {
		ReservedPairings(Set::new())
	}

	pub fn add(&mut self, r: &Reservation) {
		self.0.insert(r.clone());
	}

	pub fn union(&self, r: &Set<Reservation>) -> Self {
		ReservedPairings(self.0.union(&r).cloned().collect())
	}
}

impl std::ops::Deref for ReservedPairings {
	type Target = Set<Reservation>;

	fn deref(&self) -> &Self::Target {
		&self.0
	}
}
