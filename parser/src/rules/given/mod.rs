use crate::rules::{course, req_ref};
use crate::traits::Util;
use crate::util;
use crate::{action, filter, limit};

#[cfg(test)]
mod tests;

mod print;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
	#[serde(flatten)]
	pub given: Given,
	#[serde(default)]
	pub limit: Option<Vec<limit::Limiter>>,
	#[serde(rename = "where", default, deserialize_with = "filter::deserialize_with")]
	pub filter: Option<filter::Clause>,
	pub what: What,
	#[serde(rename = "do", deserialize_with = "util::string_or_struct_parseerror")]
	pub action: action::Action,
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		match &self.given {
			Given::NamedVariable { .. } => true,
			_ => false,
		}
	}
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(tag = "given")]
pub enum Given {
	#[serde(rename = "courses")]
	AllCourses,
	#[serde(rename = "these courses")]
	TheseCourses {
		courses: Vec<CourseRule>,
		repeats: RepeatMode,
	},
	#[serde(rename = "these requirements")]
	TheseRequirements { requirements: Vec<req_ref::Rule> },
	#[serde(rename = "areas of study")]
	AreasOfStudy,
	#[serde(rename = "save")]
	NamedVariable { save: String },
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum CourseRule {
	Value(#[serde(deserialize_with = "util::string_or_struct")] course::Rule),
}

impl crate::traits::print::Print for CourseRule {
	fn print(&self) -> crate::traits::print::Result {
		match &self {
			CourseRule::Value(v) => v.print(),
		}
	}
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum RepeatMode {
	#[serde(rename = "first")]
	First,
	#[serde(rename = "last")]
	Last,
	#[serde(rename = "all")]
	All,
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
pub enum What {
	#[serde(rename = "courses")]
	Courses,
	#[serde(rename = "distinct courses")]
	DistinctCourses,
	#[serde(rename = "credits")]
	Credits,
	#[serde(rename = "departments")]
	Departments,
	#[serde(rename = "terms")]
	Terms,
	#[serde(rename = "grades")]
	Grades,
	#[serde(rename = "areas of study")]
	AreasOfStudy,
}
