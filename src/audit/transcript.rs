use super::{MatchedParts, ReservedPairings};
use crate::rules::course::Rule as CourseRule;
use crate::student::CourseInstance;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Transcript(Vec<CourseInstance>);

impl Transcript {
	#[allow(dead_code)]
	pub fn new(courses: &[CourseInstance]) -> Self {
		Transcript(courses.to_vec())
	}
}

impl std::ops::Deref for Transcript {
	type Target = Vec<CourseInstance>;

	fn deref(&self) -> &Self::Target {
		&self.0
	}
}

impl Transcript {
	pub fn has_course_matching(
		&self,
		filter: &CourseRule,
		already_used: ReservedPairings,
	) -> Option<(CourseInstance, MatchedParts)> {
		self.0.iter().find_map(|c| {
			let m = c.matches_rule(filter);

			if already_used.contains(&(c.clone(), m.clone())) {
				return None;
			}

			if m.any_match() {
				return Some((c.clone(), m));
			}

			None
		})
	}
}
