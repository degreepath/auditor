use crate::student::{overrides, StudentData};

impl super::Requirement {
	pub fn check(&self, input: &StudentData, path: &[overrides::PathSegment]) -> RequirementResult {
		let mut path = path.to_vec();
		path.push(overrides::PathSegment::Requirement(self.name.clone()));

		if let Some(overrd) = input.overrides.iter().find(|o| o.path == path) {
			use overrides::Mode;
			match overrd.mode {
				Mode::Pass => return RequirementResult::pass(),
				Mode::AllowValue => panic!("cannot allow-value on a requirement; must be attached to a rule, instead"),
			}
		}

		if self.department_audited || self.registrar_audited {
			return RequirementResult::fail();
		}

		let mut result = RequirementResult::new();
		for requirement in &self.requirements {
			let req_result = requirement.check(&input, &path);
			result = result.update(&req_result);
		}

		// for save in &self.save {
		// 	save.check(&input, &path)
		// }

		RequirementResult {}
	}
}

#[derive(Default, Clone, Debug)]
pub struct RequirementResult {}

impl RequirementResult {
	pub fn new() -> RequirementResult {
		RequirementResult {}
	}

	pub fn update(self, _data: &RequirementResult) -> RequirementResult {
		RequirementResult {}
	}

	pub fn pass() -> RequirementResult {
		RequirementResult {}
	}

	pub fn fail() -> RequirementResult {
		RequirementResult {}
	}
}
