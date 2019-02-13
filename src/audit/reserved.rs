use super::{CourseInstance, MatchedCourseParts};
use std::collections::HashSet as Set;

pub type Reservation = (CourseInstance, MatchedCourseParts);

#[derive(Debug, Clone, Default, PartialEq)]
pub struct ReservedPairings(Set<Reservation>);

impl ReservedPairings {
	pub fn new() -> ReservedPairings {
		ReservedPairings(Set::new())
	}

	pub fn from_vec(input: &[Reservation]) -> ReservedPairings {
		ReservedPairings(input.iter().cloned().collect())
	}

	pub fn from_courses(input: &[CourseInstance]) -> ReservedPairings {
		ReservedPairings(input.iter().map(|c| (c.clone(), MatchedCourseParts::blank())).collect())
	}

	pub fn add(&mut self, r: &Reservation) {
		self.0.insert(r.clone());
	}

	pub fn union(&self, r: &Set<Reservation>) -> ReservedPairings {
		ReservedPairings(self.0.union(&r).cloned().collect())
	}
}

impl std::ops::Deref for ReservedPairings {
	type Target = Set<Reservation>;

	fn deref(&self) -> &Self::Target {
		&self.0
	}
}
