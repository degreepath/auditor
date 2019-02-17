use crate::rules::Rule;
use crate::save::SaveBlock;
use crate::util;
use serde::{Deserialize, Serialize};

mod print;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Requirement {
	pub name: String,
	#[serde(default)]
	pub message: Option<String>,
	#[serde(default = "util::serde_false")]
	pub department_audited: bool,
	#[serde(default)]
	pub result: Option<Rule>,
	#[serde(default = "util::serde_false")]
	pub contract: bool,
	#[serde(default = "util::serde_false")]
	pub registrar_audited: bool,
	#[serde(default)]
	pub save: Vec<SaveBlock>,
	#[serde(default)]
	pub requirements: Vec<Requirement>,
}
