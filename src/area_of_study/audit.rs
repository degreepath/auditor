use crate::limit::apply_limits_to_courses;
use crate::requirement::audit::RequirementResult;
use crate::student::{overrides, StudentData};

impl super::AreaOfStudy {
	pub fn check(&self, input: &StudentData) -> AreaResult {
		let mut data = input.clone();
		let courses = input.transcript.to_vec();

		// 0. remove any courses with a grade of "F"
		let courses: Vec<_> = courses.into_iter().filter(|c| !c.failed()).collect();

		// 1. apply global course limits, if given
		if let Some(limits) = &self.limits {
			let limited = apply_limits_to_courses(&limits, &courses);

			data = data.update_transcript(&limited);
		}

		let path: Vec<overrides::PathSegment> = vec![overrides::PathSegment::Root];

		let mut result = AreaResult::new();
		for requirement in &self.requirements {
			let req_result = requirement.check(&data, &path);
			result = result.update(&req_result);
		}

		result
	}
}

#[derive(Default, Clone, Debug)]
pub struct AreaResult {
	requirements: Vec<RequirementResult>,
	emphases: Vec<RequirementResult>,
}

impl AreaResult {
	pub fn new() -> AreaResult {
		AreaResult {
			requirements: vec![],
			emphases: vec![],
		}
	}

	pub fn update(self, data: &RequirementResult) -> AreaResult {
		let mut requirements = self.requirements.clone();
		requirements.push(data.clone());
		AreaResult { requirements, ..self }
	}
}
