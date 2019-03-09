use crate::filter;
use crate::limit;
use crate::rules::course;
use crate::traits::Util;
use crate::util;
use crate::value::WrappedValue;
use decorum::R32;
use serde::{Deserialize, Serialize};

// mod audit;
mod print;
#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(tag = "given", rename_all = "kebab-case")]
pub enum Rule {
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

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		match &self {
			Rule::NamedVariable { .. } => true,
			_ => false,
		}
	}
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

use util::string_or_struct_parseerror as parse;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum GivenCoursesWhatOptions {
	Courses {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<CountOnlyAction>,
	},
	DistinctCourses {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<CountOnlyAction>,
	},
	Credits {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<AnyAction>,
	},
	Subjects {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<CountOnlyAction>,
	},
	Terms {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<CountOrOrdAction>,
	},
	Grades {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<AnyAction>,
	},
}

pub fn option_t<'de, D, T>(deserializer: D) -> Result<Option<T>, D::Error>
where
	D: serde::de::Deserializer<'de>,
	T: serde::de::Deserialize<'de>,
{
	#[derive(Deserialize)]
	struct Wrapper<T>(T);

	let v = Option::deserialize(deserializer)?;
	Ok(v.map(|Wrapper(a)| a))
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum CountOnlyAction {
	Count(#[serde(deserialize_with = "parse")] WrappedValue<u64>),
}

impl crate::util::Pluralizable for CountOnlyAction {
	fn should_pluralize(&self) -> bool {
		use CountOnlyAction::*;
		match &self {
			Count(v) => v.should_pluralize(),
		}
	}
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum CountOrOrdAction {
	Count(#[serde(deserialize_with = "parse")] WrappedValue<u64>),
	Minimum,
	Maximum,
}

impl crate::util::Pluralizable for CountOrOrdAction {
	fn should_pluralize(&self) -> bool {
		use CountOrOrdAction::*;
		match &self {
			Count(v) => v.should_pluralize(),
			Maximum => false,
			Minimum => false,
		}
	}
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum AnyAction {
	Count(#[serde(deserialize_with = "parse")] WrappedValue<u64>),
	Sum(#[serde(deserialize_with = "parse")] WrappedValue<R32>),
	Average(#[serde(deserialize_with = "parse")] WrappedValue<R32>),
	Minimum,
	Maximum,
}

impl crate::util::Pluralizable for AnyAction {
	fn should_pluralize(&self) -> bool {
		use AnyAction::*;
		match &self {
			Count(v) => v.should_pluralize(),
			Sum(v) => v.should_pluralize(),
			Average(v) => v.should_pluralize(),
			Maximum => false,
			Minimum => false,
		}
	}
}

mod printable {
	use super::{AnyAction, CountOnlyAction, CountOrOrdAction};
	use crate::traits::print;
	use std::fmt::Write;

	impl print::Print for AnyAction {
		fn print(&self) -> print::Result {
			use crate::value::{TaggedValue, WrappedValue};
			use AnyAction::*;
			let mut output = String::new();

			match &self {
				Average(WrappedValue::Single(TaggedValue::GreaterThan(v))) => {
					write!(&mut output, "above {}", v.print()?)?
				}
				Average(WrappedValue::Single(TaggedValue::GreaterThanEqualTo(v))) => {
					write!(&mut output, "at or above {}", v.print()?)?
				}
				Count(v) => write!(&mut output, "{}", v.print()?)?,
				Sum(v) => write!(&mut output, "{}", v.print()?)?,
				Average(v) => write!(&mut output, "{}", v.print()?)?,
				Minimum => write!(&mut output, "the smallest item [todo]")?,
				Maximum => write!(&mut output, "the smallest item [todo]")?,
			}

			Ok(output)
		}
	}

	impl print::Print for CountOrOrdAction {
		fn print(&self) -> print::Result {
			use CountOrOrdAction::*;
			let mut output = String::new();

			match &self {
				Count(v) => write!(&mut output, "{}", v.print()?)?,
				Minimum => write!(&mut output, "the smallest item [todo]")?,
				Maximum => write!(&mut output, "the smallest item [todo]")?,
			}

			Ok(output)
		}
	}

	impl print::Print for CountOnlyAction {
		fn print(&self) -> print::Result {
			use CountOnlyAction::*;
			let mut output = String::new();

			match &self {
				Count(v) => write!(&mut output, "{}", v.print()?)?,
			}

			Ok(output)
		}
	}
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
	Areas {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<CountOnlyAction>,
	},
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum GivenPerformancesWhatOptions {
	Performances {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<CountOrOrdAction>,
	},
}

#[derive(Debug, Eq, PartialEq, Serialize, Deserialize, Clone)]
#[serde(rename_all = "kebab-case")]
pub enum GivenAttendancesWhatOptions {
	Attendances {
		#[serde(flatten, deserialize_with = "option_t")]
		action: Option<CountOrOrdAction>,
	},
}
