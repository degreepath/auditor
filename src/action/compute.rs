use super::Action;
use super::Operator;
use crate::audit::rule_result::AreaDescriptor;
use crate::audit::CourseInstance;
pub use crate::value::SingleValue;

trait ActionableData {}

impl ActionableData for CourseInstance {}
impl ActionableData for AreaDescriptor {}
impl ActionableData for u64 {}
impl ActionableData for f32 {}

impl PartialEq<SingleValue> for AreaDescriptor {
	fn eq(&self, rhs: &SingleValue) -> bool {
		false
	}
}

impl std::cmp::PartialOrd<SingleValue> for AreaDescriptor {
	fn partial_cmp(&self, other: &SingleValue) -> Option<std::cmp::Ordering> {
		None
	}
}

trait ActionResult {}
impl ActionResult for bool {}
impl ActionResult for CourseInstance {}
impl ActionResult for AreaDescriptor {}
impl ActionResult for u64 {}
impl ActionResult for f32 {}

// trait ActionsForSlice<T> {
// 	fn count(&self) -> usize;
// 	fn sum(&self) -> T;
// 	fn average(&self) -> f32;
// 	fn maximum(&self) -> Option<&T>;
// 	fn minimum(&self) -> Option<&T>;
// }

// impl<T> ActionsForSlice<T> for &[u64] {
// 	fn count(&self) -> usize {
// 		self.len()
// 	}

// 	fn sum(&self) -> u64 {
// 		self.iter().sum()
// 	}

// 	fn average(&self) -> f32 {
// 		self.sum() / self.count()
// 	}

// 	fn maximum(&self) -> Option<&u64> {
// 		self.iter().max()
// 	}

// 	fn minimum(&self) -> Option<&u64> {
// 		self.iter().min()
// 	}
// }

// impl<T> ActionsForSlice<T> for &[f32] {
// 	fn count(&self) -> usize {
// 		self.len()
// 	}

// 	fn sum(&self) -> f32 {
// 		self.iter().sum()
// 	}

// 	fn average(&self) -> f32 {
// 		self.sum() / self.count()
// 	}

// 	fn maximum(&self) -> Option<&f32> {
// 		if self.is_empty() {
// 			return None;
// 		}

// 		let mut biggest = &self[0];
// 		for item in self.iter() {
// 			biggest = &item.max(*biggest);
// 		}

// 		Some(biggest)
// 	}

// 	fn minimum(&self) -> Option<&f32> {
// 		if self.is_empty() {
// 			return None;
// 		}

// 		let mut smallest = &self[0];
// 		for item in self.iter() {
// 			smallest = &item.min(*smallest);
// 		}

// 		Some(smallest)
// 	}
// }

impl Action {
	pub fn compute<T: ActionableData>(&self, data: &[T]) -> Option<impl ActionResult>
	where
		T: PartialEq<SingleValue> + PartialOrd<SingleValue> + Eq + Ord + Clone + ActionResult,
	{
		let rhs = match &self.rhs {
			Some(v) => v,
			None => return None,
		};

		if let Count = &self.lhs {
			let lhs = data.len() as u64;
			return Some(self.cmp(&lhs, &rhs));
		} else if let Sum = &self.lhs {
			let lhs = data.iter().sum();
			return Some(self.cmp(&lhs, &rhs));
		} else if let Average = &self.lhs {
			let lhs = data.iter().sum() / (data.len() as f64);
			return Some(self.cmp(&lhs, &rhs));
		} else if let Maximum = &self.lhs {
			return data.iter().max().cloned();
		} else if let Minimum = &self.lhs {
			return data.iter().min().cloned();
		}

		None
	}

	fn cmp<T: ActionableData>(self, lhs: &T, rhs: &SingleValue) -> bool
	where
		T: PartialEq<SingleValue> + PartialOrd<SingleValue>,
	{
		match &self.op {
			Some(Operator::EqualTo) => lhs == rhs,
			Some(Operator::NotEqualTo) => lhs != rhs,
			Some(Operator::LessThan) => lhs < rhs,
			Some(Operator::LessThanEqualTo) => lhs <= rhs,
			Some(Operator::GreaterThan) => lhs > rhs,
			Some(Operator::GreaterThanEqualTo) => lhs >= rhs,
		}
	}
}
