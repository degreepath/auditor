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
	#[serde(default)]
	pub emphases: Option<Emphases>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialOrd, Ord, PartialEq, Eq, Hash)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum AreaType {
	Degree,
	Major { degree: String },
	Minor { degree: String },
	Concentration { degree: String },
	Emphasis { degree: String, major: String },
}

impl std::fmt::Display for AreaType {
	fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
		match &self {
			AreaType::Degree => write!(f, "degree"),
			AreaType::Major { .. } => write!(f, "major"),
			AreaType::Minor { .. } => write!(f, "minor"),
			AreaType::Concentration { .. } => write!(f, "concentration"),
			AreaType::Emphasis { .. } => write!(f, "emphasis"),
		}
	}
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct Emphases {
	pub limits: Vec<Limiter>,
	pub choices: Vec<Requirement>,
}
