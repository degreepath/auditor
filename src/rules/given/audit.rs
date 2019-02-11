use super::{Given, What};
use crate::audit::rule_result::AreaDescriptor;
use crate::audit::{CourseInstance, ReservedPairings, RuleAudit, RuleInput, RuleResult, RuleResultDetails, RuleStatus};
use crate::filter::Clause as Filter;
use crate::limit::Limiter;
use crate::rules::Rule as AnyRule;
use crate::value::SingleValue;

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

fn match_area_against_filter(area: &AreaDescriptor, filter: &Filter) -> bool {
	true
}

impl super::Rule {
	fn apply_action<T>(&self, data: &[T]) -> RuleStatus
	where
		T: Ord + PartialEq<SingleValue> + PartialOrd<SingleValue>,
	{
		let result = self.action.compute(data);

		RuleStatus::Pass
	}
}

impl super::Rule {
	fn check_for_areas(&self, input: &RuleInput) -> RuleResult {
		use Given::*;

		let mut areas = match &self.given {
			AreasOfStudy => self.in_areas(input),
			TheseRequirements { requirements } => self.in_requirements_out_areas(input, requirements),
			NamedVariable { save } => self.in_variable_out_areas(input, save),
		};

		if let Some(filter) = self.filter {
			areas = areas
				.into_iter()
				.filter(|area| match_area_against_filter(&area, &filter))
				.collect();
		}

		if let Some(limits) = self.limit {
			use std::collections::BTreeMap;
			let limiters: BTreeMap<Limiter, u64> = BTreeMap::new();

			let areas_which_passed_the_limits = Vec::new();

			for area in areas {
				let mut area_allowed = true;
				for limiter in limits {
					if match_area_against_filter(&area, &limiter.filter) {
						limiters.entry(limiter).and_modify(|count| *count += 1).or_insert(0);

						if limiters.get(&limiter).unwrap() > &limiter.at_most {
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

		let status = self.apply_action(&areas);

		use crate::audit::rule_result::GivenOutput;

		RuleResult {
			status,
			reservations: ReservedPairings::new(),
			detail: RuleResultDetails::Given(Some(
				areas.iter().map(|a| GivenOutput::AreaOfStudy(a.clone())).collect(),
			)),
		}
	}

	fn check_for_courses(&self, input: &RuleInput) -> RuleResult {
		use Given::*;

		let courses = match &self.given {
			AllCourses => self.in_all_courses(input),
			TheseCourses { courses, repeats } => self.in_these_courses(input, courses, repeats),
			TheseRequirements { requirements } => self.in_requirements_out_courses(input, requirements),
			NamedVariable { save } => self.in_variable_out_courses(input, save),
		};

		RuleResult {
			status: RuleStatus::Pending,
			reservations: ReservedPairings::new(),
			detail: RuleResultDetails::Given(None),
		}
	}

	fn in_all_courses(&self, input: &RuleInput) -> Vec<CourseInstance> {
		vec![]
	}

	fn in_these_courses(
		&self,
		input: &RuleInput,
		these_courses: &[super::CourseRule],
		repeats: &super::RepeatMode,
	) -> Vec<CourseInstance> {
		vec![]
	}

	fn in_areas(&self, input: &RuleInput) -> Vec<AreaDescriptor> {
		vec![]
	}

	fn in_requirements_out_courses(
		&self,
		input: &RuleInput,
		these_requirements: &[super::req_ref::Rule],
	) -> Vec<CourseInstance> {
		vec![]
	}

	fn in_requirements_out_areas(
		&self,
		input: &RuleInput,
		these_requirements: &[super::req_ref::Rule],
	) -> Vec<AreaDescriptor> {
		vec![]
	}

	fn in_variable_out_courses(&self, input: &RuleInput, save: &str) -> Vec<CourseInstance> {
		vec![]
	}

	fn in_variable_out_areas(&self, input: &RuleInput, save: &str) -> Vec<AreaDescriptor> {
		vec![]
	}
}
