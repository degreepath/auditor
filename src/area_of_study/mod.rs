use crate::limit::Limiter;
use crate::requirement::Requirement;
use crate::rules::Rule;
use serde::{Deserialize, Serialize};

mod attributes;
mod audit;
mod print;
#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct AreaOfStudy {
	#[serde(rename = "name")]
	pub area_name: String,
	#[serde(flatten)]
	pub area_type: AreaType,
	#[serde(default)]
	pub institution: Option<String>,
	pub catalog: String,
	pub result: Rule,
	pub requirements: Vec<Requirement>,
	#[serde(default)]
	pub attributes: Option<attributes::Attributes>,
	#[serde(default)]
	pub limits: Option<Vec<Limiter>>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialOrd, Ord, PartialEq, Eq)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum AreaType {
	Degree,
	Major { degree: String },
	Minor { degree: String },
	Concentration { degree: String },
	Emphasis { degree: String, major: String },
}
