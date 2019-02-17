use crate::filterable_data::DataValue;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// MatchedCourseParts reflects the _course_, not the matching rule or filter.
/// That is, its values are those that _were matched_ from the course.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct MatchedParts(BTreeMap<String, MatchType<DataValue>>);

impl std::ops::Deref for MatchedParts {
	type Target = BTreeMap<String, MatchType<DataValue>>;

	fn deref(&self) -> &Self::Target {
		&self.0
	}
}

#[allow(dead_code)]
impl MatchedParts {
	pub fn new(data: &BTreeMap<String, MatchType<DataValue>>) -> MatchedParts {
		MatchedParts(data.clone())
	}

	pub fn blank() -> MatchedParts {
		MatchedParts(BTreeMap::new())
	}

	pub fn any(&self) -> bool {
		self.0.values().any(|v| v.matched())
	}

	pub fn all(&self) -> bool {
		self.0.values().all(|v| v.matched())
	}
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum MatchType<T> {
	Match(T),
	Skip,
	Fail,
}

impl<T> MatchType<T> {
	pub fn matched(&self) -> bool {
		match &self {
			MatchType::Match(_) => true,
			_ => false,
		}
	}

	#[allow(dead_code)]
	pub fn skipped(&self) -> bool {
		match &self {
			MatchType::Skip => true,
			_ => false,
		}
	}

	#[allow(dead_code)]
	pub fn failed(&self) -> bool {
		match &self {
			MatchType::Fail => true,
			_ => false,
		}
	}
}
