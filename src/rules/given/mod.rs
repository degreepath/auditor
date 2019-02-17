use crate::rules::{course, req_ref};
use crate::traits::Util;
use crate::util;
use crate::{action, filter, limit};
use serde::{Deserialize, Serialize};

mod audit;
mod print;
#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
	#[serde(flatten)]
	pub given: Given,
	#[serde(default)]
	pub limit: Option<Vec<limit::Limiter>>,
	#[serde(rename = "where", default, deserialize_with = "filter::deserialize_with")]
	pub filter: Option<filter::Clause>,
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
#[serde(tag = "given", rename_all = "kebab-case")]
pub enum Given {
	#[serde(rename = "courses")]
	AllCourses {
		what: GivenCoursesWhatOptions,
	},
	TheseCourses {
		courses: Vec<CourseRule>,
		repeats: RepeatMode,
		what: GivenCoursesWhatOptions,
	},
	TheseRequirements {
		requirements: Vec<req_ref::Rule>,
		what: GivenCoursesWhatOptions,
	},
	Areas {
		what: GivenAreasWhatOptions,
	},
	#[serde(rename = "save")]
	NamedVariable {
		save: String,
		what: GivenCoursesWhatOptions,
	},
	Performances {
		what: GivenPerformancesWhatOptions,
	},
	Attendances {
		what: GivenAttendancesWhatOptions,
	},
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(tag = "given", rename_all = "kebab-case")]
pub enum GivenForSaveBlock {
	#[serde(rename = "courses")]
	AllCourses { what: GivenCoursesWhatOptions },
	TheseCourses {
		courses: Vec<CourseRule>,
		repeats: RepeatMode,
		what: GivenCoursesWhatOptions,
	},
	TheseRequirements {
		requirements: Vec<req_ref::Rule>,
		what: GivenCoursesWhatOptions,
	},
	#[serde(rename = "save")]
	NamedVariable {
		save: String,
		what: GivenCoursesWhatOptions,
	},
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum GivenCoursesWhatOptions {
	Courses,
	DistinctCourses,
	Credits,
	Departments,
	Terms,
	Grades,
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

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum RepeatMode {
	First,
	Last,
	All,
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum GivenAreasWhatOptions {
	Areas,
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum GivenPerformancesWhatOptions {
	Performances,
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum GivenAttendancesWhatOptions {
	Attendances,
}
