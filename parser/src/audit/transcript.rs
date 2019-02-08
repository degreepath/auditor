use super::{CourseInstance, MatchedCourseParts, ReservedPairings};
use crate::rules::course::Rule as CourseRule;

#[derive(Debug, Clone)]
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
	) -> Option<(CourseInstance, MatchedCourseParts)> {
		for c in self.iter() {
			let m = c.matches_filter(filter);
			if already_used.contains(&(c.clone(), filter.clone(), m.clone())) {
				continue;
			}
			if m.any() {
				return Some((c.clone(), m));
			}
		}
		None
	}
}
