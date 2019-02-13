use super::{Given, What};
use crate::audit::rule_result::AreaDescriptor;
use crate::audit::{
	CourseInstance, MatchedCourseParts, Reservation, ReservedPairings, RuleAudit, RuleInput, RuleResult,
	RuleResultDetails,
};
use crate::filter::Clause as Filter;
use crate::limit::Limiter;
use crate::rules::Rule as AnyRule;

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
		use What::*;

		match &self.what {
			AreasOfStudy => self.check_for_areas(input),
			Courses | DistinctCourses | Credits | Departments | Terms | Grades => self.check_for_courses(input),
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
	fn check_for_areas(&self, input: &RuleInput) -> RuleResult {
		use Given::*;

		let mut areas = match &self.given {
			AreasOfStudy => self.in_areas(input),
			TheseRequirements { requirements } => self.in_requirements_out_areas(input, requirements),
			NamedVariable { save } => self.in_variable_out_areas(input, save),
			AllCourses => unimplemented!("check_for_areas should not be given:all-courses"),
			TheseCourses { .. } => unimplemented!("check_for_areas should not be given:these-courses"),
		};

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

	fn check_for_courses(&self, input: &RuleInput) -> RuleResult {
		use crate::audit::course_match::MatchedCourseParts;
		use Given::*;

		let courses = match &self.given {
			AllCourses => self.in_all_courses(input),
			TheseCourses { courses, repeats } => self.in_these_courses(input, courses, repeats),
			TheseRequirements { requirements } => self.in_requirements_out_courses(input, requirements),
			NamedVariable { save } => self.in_variable_out_courses(input, save),
			AreasOfStudy => unimplemented!("check_for_courses should not be given:areas"),
		};

		let mut courses: Vec<Reservation> = courses.into_iter().map(|c| (c, MatchedCourseParts::blank())).collect();

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

	fn in_all_courses(&self, input: &RuleInput) -> Vec<CourseInstance> {
		input.transcript.to_vec()
	}

	fn in_these_courses(
		&self,
		input: &RuleInput,
		these_courses: &[super::CourseRule],
		repeats: &super::RepeatMode,
	) -> Vec<CourseInstance> {
		use super::CourseRule as GivenCourseRuleWrapper;
		use super::RepeatMode;
		use std::collections::HashSet;

		let mut matching_courses = vec![];
		let mut matched_course_ids: HashSet<String> = HashSet::new();

		for course in &input.transcript.into_iter() {
			match repeats {
				RepeatMode::All => (),
				RepeatMode::First => {
					if matched_course_ids.contains(&course.course) {
						continue;
					}
				}
			};

			if these_courses.iter().any(|rule| match rule {
				GivenCourseRuleWrapper::Value(rule) => course.matches_rule(rule).any(),
			}) {
				matching_courses.push(course);
				matched_course_ids.insert(course.course.clone());
			}
		}

		matching_courses
	}

	fn in_areas(&self, _input: &RuleInput) -> Vec<AreaDescriptor> {
		vec![]
	}

	fn in_requirements_out_courses(
		&self,
		_input: &RuleInput,
		_these_requirements: &[super::req_ref::Rule],
	) -> Vec<CourseInstance> {
		vec![]
	}

	fn in_requirements_out_areas(
		&self,
		_input: &RuleInput,
		_these_requirements: &[super::req_ref::Rule],
	) -> Vec<AreaDescriptor> {
		vec![]
	}

	fn in_variable_out_courses(&self, _input: &RuleInput, _save: &str) -> Vec<CourseInstance> {
		vec![]
	}

	fn in_variable_out_areas(&self, _input: &RuleInput, _save: &str) -> Vec<AreaDescriptor> {
		vec![]
	}
}
