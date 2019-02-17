use super::Given;
use crate::audit::{
	CourseInstance, MatchedCourseParts, ReservedPairings, RuleAudit, RuleInput, RuleResult, RuleResultDetails,
};
use crate::filter::Clause as Filter;
use crate::limit::Limiter;
use crate::rules::{req_ref, Rule as AnyRule};
use crate::student::AreaDescriptor;

impl super::Rule {
	pub fn to_rule(&self) -> AnyRule {
		AnyRule::Given(self.clone())
	}
}

/// rough implementation plan:
/// 1. pick the appropriate type of input
///     1. if "courses"
///         1. if "first", remove duplicate courses from the input,
///            leaving only the first one chronologically;
///         2. if "all", do not remove any courses
///     2. if "these-courses"
///         1. find the intersection between the transcript and the given courses
///
/// 2. apply the filter to each item of the input
///
/// 3. iterate over the input, keeping track of which limiters apply
///        to which items, and removing items past the limit
///
/// 4. collect the requested item type into the output vector
///     1. if "courses": .map(|c| c)
///     2. if "terms": .map(|c| c.term)
///     3. if "grades": .map(|c| c.grade)
///
/// 5. apply the action to the output vector
impl RuleAudit for super::Rule {
	fn check(&self, input: &RuleInput) -> RuleResult {
		match &self.given {
			Given::AllCourses { what: _ } => {
				let data = self.in_all_courses(input);
				self.check_for_courses(input, &data)
			}
			Given::TheseCourses {
				what: _,
				courses,
				repeats,
			} => {
				let data = self.in_these_courses(input, courses, repeats);
				self.check_for_courses(input, &data)
			}
			Given::TheseRequirements { what: _, requirements } => {
				let data = self.in_requirements_out_courses(input, requirements);
				self.check_for_courses(input, &data)
			}
			Given::NamedVariable { save, what: _ } => {
				let data = self.in_variable_out_courses(input, save);
				self.check_for_courses(input, &data)
			}
			Given::Areas { what: _ } => {
				let data = self.in_areas(input);
				self.check_for_areas(input, &data)
			}
			Given::Performances { what: _ } => unimplemented!("performances"),
			Given::Attendances { what: _ } => unimplemented!("attendances"),
		}
	}
}

fn match_area_against_filter(_area: &AreaDescriptor, _filter: &Filter) -> bool {
	true
}

fn match_course_against_filter(_course: &CourseInstance, _filter: &Filter) -> Option<MatchedCourseParts> {
	Some(MatchedCourseParts::blank())
}

use crate::audit::rule_result::{GivenOutput, GivenOutputType};

impl super::Rule {
	fn check_for_areas(&self, _input: &RuleInput, areas: &[AreaDescriptor]) -> RuleResult {
		let mut areas: Vec<_> = areas.iter().cloned().collect();

		if let Some(filter) = &self.filter {
			areas = areas
				.into_iter()
				.filter(|area| match_area_against_filter(&area, &filter))
				.collect();
		}

		if let Some(limits) = &self.limit {
			use std::collections::BTreeMap;
			let mut limiters: BTreeMap<&Limiter, u64> = BTreeMap::new();

			let mut areas_which_passed_the_limits = Vec::new();

			for area in areas {
				let mut area_allowed = true;
				for limiter in limits.iter() {
					if match_area_against_filter(&area, &limiter.filter) {
						limiters.entry(&limiter).and_modify(|count| *count += 1).or_insert(1);

						if limiters[limiter] > limiter.at_most {
							area_allowed = false;
						}
					}
				}

				if area_allowed {
					areas_which_passed_the_limits.push(area);
				}
			}

			areas = areas_which_passed_the_limits;
		}

		let status = self.action.compute_with_areas(&areas).status;

		RuleResult {
			status,
			reservations: ReservedPairings::new(),
			detail: RuleResultDetails::Given(GivenOutputType::MultiValue(
				areas.iter().map(|a| GivenOutput::AreaOfStudy(a.clone())).collect(),
			)),
		}
	}

	fn check_for_courses(&self, _input: &RuleInput, courses: &ReservedPairings) -> RuleResult {
		let mut courses: Vec<_> = courses.iter().cloned().collect();

		if let Some(filter) = &self.filter {
			courses = courses
				.into_iter()
				.filter_map(|(course, _)| match match_course_against_filter(&course, &filter) {
					Some(match_info) => Some((course, match_info)),
					None => None,
				})
				.collect();
		}

		if let Some(limits) = &self.limit {
			use std::collections::BTreeMap;
			let mut limiters: BTreeMap<&Limiter, u64> = BTreeMap::new();

			let mut items_which_passed_the_limits = Vec::new();

			for (course, match_info) in courses {
				let mut course_allowed = true;

				for limiter in limits.iter() {
					// during limitation application, we don't care about what parts of a course
					// matched – we just care that _something_ matched
					if match_course_against_filter(&course, &limiter.filter).is_some() {
						limiters.entry(&limiter).and_modify(|count| *count += 1).or_insert(1);

						if limiters[limiter] > limiter.at_most {
							course_allowed = false;
						}
					}
				}

				if course_allowed {
					items_which_passed_the_limits.push((course, match_info));
				}
			}

			courses = items_which_passed_the_limits;
		}

		let only_the_courses: Vec<_> = courses.iter().map(|(c, _)| c).cloned().collect();
		let computed = self.action.compute_with_courses(&only_the_courses);

		RuleResult {
			status: computed.status,
			reservations: ReservedPairings::from_vec(&courses),
			detail: RuleResultDetails::Given(GivenOutputType::MultiValue(
				only_the_courses.iter().cloned().map(GivenOutput::Course).collect(),
			)),
		}
	}

	fn in_all_courses(&self, input: &RuleInput) -> ReservedPairings {
		ReservedPairings::from_courses(&input.data.transcript)
	}

	fn in_these_courses(
		&self,
		input: &RuleInput,
		allowed_courses: &[super::CourseRule],
		repeats: &super::RepeatMode,
	) -> ReservedPairings {
		use super::CourseRule as GivenCourseRuleWrapper;
		use super::RepeatMode;

		let courses = input.data.transcript.to_vec();
		let courses = match repeats {
			RepeatMode::All => courses,
			RepeatMode::First => {
				// sort by term; take the first occurrence of each course
				let mut courses = courses;
				courses.sort_unstable_by_key(|c| (c.course.clone(), c.term.clone()));
				courses.dedup_by_key(|c| (c.course.clone(), c.term.clone()));
				courses
			}
			RepeatMode::Last => {
				// sort by term; take the last occurrence of each course
				let mut courses = courses;
				courses.sort_unstable_by_key(|c| (c.course.clone(), c.term.clone()));
				courses.reverse();
				courses.dedup_by_key(|c| (c.course.clone(), c.term.clone()));
				courses
			}
		};

		let allowed_courses: Vec<_> = allowed_courses
			.iter()
			.map(|rule| match rule {
				GivenCourseRuleWrapper::Value(rule) => rule,
			})
			.collect();

		// essentially, given courses from the transcript, find the intersection between them and
		// the listed "allowed" courses
		let courses: Vec<_> = courses
			.into_iter()
			.filter(|course| allowed_courses.iter().any(|rule| course.matches_rule(rule).any()))
			.collect();

		ReservedPairings::from_courses(&courses)
	}

	fn in_areas(&self, _input: &RuleInput) -> Vec<AreaDescriptor> {
		vec![]
	}

	fn in_requirements_out_courses(&self, input: &RuleInput, these_requirements: &[req_ref::Rule]) -> ReservedPairings {
		let collected: Vec<_> = these_requirements
			.iter()
			.filter_map(|req_ref| {
				input
					.completed_siblings
					.get(&req_ref.requirement)
					.map(|req| req.reservations.iter().collect::<Vec<_>>())
			})
			.flatten()
			.cloned()
			.collect();

		ReservedPairings::from_vec(&collected)
	}

	fn in_variable_out_courses(&self, _input: &RuleInput, _save: &str) -> ReservedPairings {
		ReservedPairings::new()
	}
}
