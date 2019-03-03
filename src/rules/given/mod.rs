use crate::rules::course;
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
		#[serde(rename = "where", default)]
		filter: Option<filter::CourseClause>,
		#[serde(default)]
		limit: Option<Vec<limit::Limiter>>,
	},
	TheseCourses {
		courses: Vec<CourseRule>,
		repeats: RepeatMode,
		what: GivenCoursesWhatOptions,
		#[serde(rename = "where", default)]
		filter: Option<filter::CourseClause>,
		#[serde(default)]
		limit: Option<Vec<limit::Limiter>>,
	},
	TheseRequirements {
		requirements: Vec<String>,
		what: GivenCoursesWhatOptions,
		#[serde(rename = "where", default)]
		filter: Option<filter::CourseClause>,
		#[serde(default)]
		limit: Option<Vec<limit::Limiter>>,
	},
	Areas {
		what: GivenAreasWhatOptions,
		#[serde(rename = "where", default)]
		filter: Option<filter::AreaClause>,
	},
	#[serde(rename = "save")]
	NamedVariable {
		save: String,
		what: GivenCoursesWhatOptions,
		#[serde(rename = "where", default)]
		filter: Option<filter::CourseClause>,
		#[serde(default)]
		limit: Option<Vec<limit::Limiter>>,
	},
	Performances {
		what: GivenPerformancesWhatOptions,
		#[serde(rename = "where", default)]
		filter: Option<filter::PerformanceClause>,
	},
	Attendances {
		what: GivenAttendancesWhatOptions,
		#[serde(rename = "where", default)]
		filter: Option<filter::AttendanceClause>,
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
		requirements: Vec<String>,
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
