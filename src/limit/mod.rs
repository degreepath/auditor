use crate::filter;
use crate::filter::{match_area_against_filter, match_course_against_filter};
use crate::student::{AreaDescriptor, CourseInstance};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Hash, Eq, Ord, PartialOrd)]
#[serde(deny_unknown_fields)]
pub struct Limiter {
	#[serde(rename = "where", deserialize_with = "filter::deserialize_with_no_option")]
	pub filter: filter::Clause,
	pub at_most: u64,
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

pub fn apply_limits_to_areas(limits: &[Limiter], areas: &[AreaDescriptor]) -> Vec<AreaDescriptor> {
	let mut limiters: BTreeMap<&Limiter, u64> = BTreeMap::new();

	areas
		.iter()
		.filter(|course| {
			for limiter in limits.iter() {
				if match_area_against_filter(&course, &limiter.filter) {
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
