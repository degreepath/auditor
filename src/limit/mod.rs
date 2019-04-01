use crate::filter;
use serde::{Deserialize, Serialize};

#[cfg(test)]
mod tests;

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd)]
#[serde(deny_unknown_fields)]
pub struct Limiter {
	pub at_most: u64,
	#[serde(rename = "where")]
	pub filter: filter::CourseClause,
}
