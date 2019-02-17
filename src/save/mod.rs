use crate::rules::given::GivenForSaveBlock;
use crate::{action, filter, limit};
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
	#[serde(rename = "where", default, deserialize_with = "filter::deserialize_with")]
	pub filter: Option<filter::Clause>,
	#[serde(rename = "do", default, deserialize_with = "action::option_action")]
	pub action: Option<action::Action>,
}
