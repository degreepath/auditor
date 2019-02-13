use crate::filter;
use serde::{Deserialize, Serialize};

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Hash, Eq, Ord, PartialOrd)]
#[serde(deny_unknown_fields)]
pub struct Limiter {
	#[serde(rename = "where", deserialize_with = "filter::deserialize_with_no_option")]
	pub filter: filter::Clause,
	pub at_most: u64,
}
