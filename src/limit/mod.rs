use crate::filter;
use crate::filter::match_course_against_filter;
use crate::student::CourseInstance;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[cfg(test)]
mod tests;

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd)]
#[serde(deny_unknown_fields)]
pub struct Limiter {
	pub at_most: u64,
	#[serde(rename = "where")]
	pub filter: filter::CourseClause,
}

pub fn apply_limits_to_courses(limits: &[Limiter], courses: &[CourseInstance]) -> Vec<CourseInstance> {
	let mut limiters: BTreeMap<&Limiter, u64> = BTreeMap::new();

	courses
		.iter()
		.filter(|course| {
			for limiter in limits.iter() {
				// during limitation application, we don't care about what parts of a course
				// matched – we just care that _something_ matched
				if match_course_against_filter(&course, &limiter.filter).is_some() {
					limiters.entry(&limiter).and_modify(|count| *count += 1).or_insert(1);

					if limiters[limiter] > limiter.at_most {
						return false;
					}
				}
			}

			true
		})
		.cloned()
		.collect()
}
