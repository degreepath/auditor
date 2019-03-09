use crate::student::{AreaDescriptor, CourseInstance};
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
