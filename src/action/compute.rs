use super::Action;
use super::Operator;
use crate::audit::rule_result::{GivenOutput, GivenOutputType, RuleStatus};
use crate::audit::CourseInstance;
use crate::student::AreaDescriptor;
pub use crate::value::SingleValue;

pub(crate) trait ActionableData {}

impl ActionableData for CourseInstance {}
impl ActionableData for AreaDescriptor {}
impl ActionableData for u64 {}
impl ActionableData for f32 {}

impl PartialEq<SingleValue> for AreaDescriptor {
	fn eq(&self, _rhs: &SingleValue) -> bool {
		false
	}
}

impl std::cmp::PartialOrd<SingleValue> for AreaDescriptor {
	fn partial_cmp(&self, _other: &SingleValue) -> Option<std::cmp::Ordering> {
		None
	}
}

trait CustomMaxMinOnFloatVecs {
	fn custom_max(&self) -> Option<f32>;
	fn custom_min(&self) -> Option<f32>;
}

impl CustomMaxMinOnFloatVecs for Vec<f32> {
	fn custom_max(&self) -> Option<f32> {
		if self.is_empty() {
			return None;
		}

		let mut extreme: f32 = self[0];
		for item in self.iter() {
			extreme = item.max(extreme);
		}

		Some(extreme)
	}

	fn custom_min(&self) -> Option<f32> {
		if self.is_empty() {
			return None;
		}

		let mut extreme: f32 = self[0];
		for item in self.iter() {
			extreme = item.max(extreme);
		}

		Some(extreme)
	}
}

impl Action {
	pub(crate) fn cmp<T: ActionableData>(self, lhs: &T, rhs: &SingleValue) -> bool
	where
		T: PartialEq<SingleValue> + PartialOrd<SingleValue>,
	{
		if self.op.is_none() {
			unimplemented!("should not be able to call self.cmp on a None action operator")
		}

		match &self.op.unwrap() {
			Operator::EqualTo => lhs == rhs,
			Operator::NotEqualTo => lhs != rhs,
			Operator::LessThan => lhs < rhs,
			Operator::LessThanEqualTo => lhs <= rhs,
			Operator::GreaterThan => lhs > rhs,
			Operator::GreaterThanEqualTo => lhs >= rhs,
		}
	}
}

pub struct GivenActionResult {
	pub status: RuleStatus,
	pub detail: GivenOutputType,
}

impl Action {
	pub fn compute_with_areas(&self, data: &[AreaDescriptor]) -> GivenActionResult {
		use crate::action::Command::*;

		let rhs = match &self.rhs {
			Some(v) => v,
			None => unimplemented!("empty-rhs rule evaluation"),
		};

		match &self.lhs {
			Count => {
				let lhs = data.len() as u64;
				let result = self.clone().cmp(&lhs, &rhs);

				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Count(lhs),
				}
			}
			Sum => unimplemented!("sum-action on area descriptor"),
			Average => unimplemented!("average-action on area descriptor"),
			Maximum => unimplemented!("maximum-action on area descriptor"),
			Minimum => unimplemented!("minimum-action on area descriptor"),
		}
	}

	pub fn compute_with_departments(&self, data: &[&str]) -> GivenActionResult {
		use crate::action::Command::*;

		let rhs = match &self.rhs {
			Some(v) => v,
			None => unimplemented!("empty-rhs rule evaluation"),
		};

		match &self.lhs {
			Count => {
				let lhs = data.len() as u64;
				let result = self.clone().cmp(&lhs, &rhs);

				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Count(lhs),
				}
			}
			Sum => unimplemented!("sum-action on department"),
			Average => unimplemented!("average-action on department"),
			Maximum => unimplemented!("maximum-action on department"),
			Minimum => unimplemented!("minimum-action on department"),
		}
	}

	pub fn compute_with_terms(&self, data: &[u64]) -> GivenActionResult {
		use crate::action::Command::*;

		let rhs = match &self.rhs {
			Some(v) => v,
			None => unimplemented!("empty-rhs rule evaluation"),
		};

		match &self.lhs {
			Count => {
				let lhs = data.len() as u64;
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Count(lhs),
				}
			}
			Sum => {
				let lhs: u64 = data.iter().sum();
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::SumInteger(lhs),
				}
			}
			Average => {
				let lhs: f32 = data.iter().sum::<u64>() as f32 / (data.len() as f32);
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Average(lhs),
				}
			}
			Maximum => {
				let lhs = data.iter().max().cloned();
				GivenActionResult {
					status: RuleStatus::Pass,
					detail: GivenOutputType::Max(Box::new(lhs.map(GivenOutput::Term))),
				}
			}
			Minimum => {
				let lhs = data.iter().min().cloned();
				GivenActionResult {
					status: RuleStatus::Pass,
					detail: GivenOutputType::Min(Box::new(lhs.map(GivenOutput::Term))),
				}
			}
		}
	}

	pub fn compute_with_credits(&self, data: &[f32]) -> GivenActionResult {
		use crate::action::Command::*;

		let rhs = match &self.rhs {
			Some(v) => v,
			None => unimplemented!("empty-rhs rule evaluation"),
		};

		match &self.lhs {
			Count => {
				let lhs = data.len() as u64;
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Count(lhs),
				}
			}
			Sum => {
				let lhs: f32 = data.iter().sum();
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::SumFloat(lhs),
				}
			}
			Average => {
				let lhs: f32 = data.iter().sum::<f32>() as f32 / (data.len() as f32);
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Average(lhs),
				}
			}
			Maximum => {
				let lhs = data.to_vec().custom_max();
				GivenActionResult {
					status: RuleStatus::Pass,
					detail: GivenOutputType::Max(Box::new(lhs.map(GivenOutput::Credit))),
				}
			}
			Minimum => {
				let lhs = data.to_vec().custom_min();
				GivenActionResult {
					status: RuleStatus::Pass,
					detail: GivenOutputType::Min(Box::new(lhs.map(GivenOutput::Credit))),
				}
			}
		}
	}

	pub fn compute_with_grades(&self, data: &[f32]) -> GivenActionResult {
		use crate::action::Command::*;

		let rhs = match &self.rhs {
			Some(v) => v,
			None => unimplemented!("empty-rhs rule evaluation"),
		};

		match &self.lhs {
			Count => {
				let lhs = data.len() as u64;
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Count(lhs),
				}
			}
			Sum => {
				let lhs: f32 = data.iter().sum();
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::SumFloat(lhs),
				}
			}
			Average => {
				let lhs: f32 = data.iter().sum::<f32>() as f32 / (data.len() as f32);
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Average(lhs),
				}
			}
			Maximum => {
				let lhs = data.to_vec().custom_max();
				GivenActionResult {
					status: RuleStatus::Pass,
					detail: GivenOutputType::Max(Box::new(lhs.map(GivenOutput::Grade))),
				}
			}
			Minimum => {
				let lhs = data.to_vec().custom_min();
				GivenActionResult {
					status: RuleStatus::Pass,
					detail: GivenOutputType::Min(Box::new(lhs.map(GivenOutput::Grade))),
				}
			}
		}
	}

	pub fn compute_with_courses(&self, data: &[CourseInstance]) -> GivenActionResult {
		use crate::action::Command::*;

		let rhs = match &self.rhs {
			Some(v) => v,
			None => unimplemented!("empty-rhs rule evaluation"),
		};

		match &self.lhs {
			Count => {
				let lhs = data.len() as u64;
				let result = self.clone().cmp(&lhs, &rhs);
				GivenActionResult {
					status: if result { RuleStatus::Pass } else { RuleStatus::Fail },
					detail: GivenOutputType::Count(lhs),
				}
			}
			Sum => unimplemented!("sum-action on course instances"),
			Average => unimplemented!("average-action on course instances"),
			Maximum => unimplemented!("max-action on course instances"),
			Minimum => unimplemented!("min-action on course instances"),
		}
	}
}
