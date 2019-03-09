use crate::filter;
use crate::limit;
use crate::rules::given::GivenForSaveBlock;
use serde::{Deserialize, Serialize};

mod print;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct SaveBlock {
	pub name: String,
	#[serde(flatten)]
	pub given: GivenForSaveBlock,
	#[serde(default)]
	pub limit: Option<Vec<limit::Limiter>>,
	#[serde(rename = "where", default)]
	pub filter: Option<filter::CourseClause>,
}
