use crate::limit::apply_limits_to_courses;
use crate::requirement::audit::RequirementResult;
use crate::student::{overrides, StudentData};

impl super::AreaOfStudy {
	pub fn check(&self, input: &StudentData) -> AreaResult {
		let mut data = input.clone();

		// 0. remove any courses with a grade of "F"

		// 1. apply global course limits, if given
		if let Some(limits) = &self.limits {
			let courses = input.transcript.to_vec();
			let courses = apply_limits_to_courses(&limits, &courses);

			data = data.update_transcript(&courses);
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
