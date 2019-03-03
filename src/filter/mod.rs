use crate::audit::course_match::MatchedParts;
use crate::student::{AreaDescriptor, CourseInstance, CourseType, GradeOption, Semester};
use crate::value::WrappedValue as Value;
use decorum::R32;
use serde::{Deserialize, Serialize};

mod constant;
mod print;
#[cfg(test)]
mod tests;

// #[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd)]
// pub enum Clause {
// 	Course(CourseClause),
// 	Area(AreaClause),
// 	Performance(PerformanceClause),
// 	Attendance(AttendanceClause),
// 	Organization(OrganizationClause),
// }

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(deny_unknown_fields)]
pub struct CourseClause {
	pub attribute: Option<Value<String>>,
	pub course: Option<Value<String>>,
	pub credits: Option<Value<R32>>,
	pub gereqs: Option<Value<String>>,
	pub graded: Option<Value<GradeOption>>,
	pub institution: Option<Value<String>>,
	pub level: Option<Value<u64>>,
	pub number: Option<Value<u64>>,
	pub r#type: Option<Value<CourseType>>,
	pub semester: Option<Value<Semester>>,
	pub subject: Option<Value<String>>,
	pub year: Option<Value<ClassificationYear>>,
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd)]
#[serde(rename_all = "kebab-case")]
pub enum ClassificationYear {
	SecondYear,
	FourthYear,
	JuniorYear,
	SeniorYear,
	GraduationYear,
}

impl std::str::FromStr for ClassificationYear {
	type Err = crate::util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		use crate::util::ParseError;

		match s.trim() {
			"second-year" => Ok(ClassificationYear::SecondYear),
			"fourth-year" => Ok(ClassificationYear::FourthYear),
			"junior-year" => Ok(ClassificationYear::JuniorYear),
			"senior-year" => Ok(ClassificationYear::SeniorYear),
			"graduation-year" => Ok(ClassificationYear::GraduationYear),
			_ => Err(ParseError::InvalidValue),
		}
	}
}

impl crate::traits::print::Print for ClassificationYear {
	fn print(&self) -> crate::traits::print::Result {
		Ok(match &self {
			ClassificationYear::GraduationYear => "graduation year".to_string(),
			ClassificationYear::SeniorYear => "senior year".to_string(),
			ClassificationYear::JuniorYear => "junior year".to_string(),
			ClassificationYear::FourthYear => "fourth year".to_string(),
			ClassificationYear::SecondYear => "second year".to_string(),
		})
	}
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(tag = "type", rename_all = "lowercase")]
#[serde(deny_unknown_fields)]
pub struct AreaClause {
	name: Option<Value<String>>,
	r#type: Option<Value<AreaType>>,
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd)]
pub enum AreaType {
	Degree,
	Major,
	Minor,
	Concentration,
	Emphasis,
}

impl crate::traits::print::Print for AreaType {
	fn print(&self) -> crate::traits::print::Result {
		Ok(match &self {
			AreaType::Degree => "degree".to_string(),
			AreaType::Major => "major".to_string(),
			AreaType::Minor => "minor".to_string(),
			AreaType::Concentration => "concentration".to_string(),
			AreaType::Emphasis => "emphasis".to_string(),
		})
	}
}

use crate::value::{TaggedValue, WrappedValue};
impl PartialEq<AreaType> for WrappedValue<AreaType> {
	fn eq(&self, rhs: &AreaType) -> bool {
		match &self {
			WrappedValue::Single(value) => value == rhs,
			WrappedValue::Or(vec) => vec.iter().any(|v| v == rhs),
			WrappedValue::And(vec) => vec.iter().all(|v| v == rhs),
		}
	}
}

impl PartialEq<AreaType> for TaggedValue<AreaType> {
	fn eq(&self, rhs: &AreaType) -> bool {
		match &self {
			TaggedValue::EqualTo(value) => value == rhs,
			TaggedValue::NotEqualTo(value) => value != rhs,
			_ => unimplemented!(),
		}
	}
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(deny_unknown_fields)]
pub struct PerformanceClause {
	pub name: Option<Value<String>>,
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(deny_unknown_fields)]
pub struct AttendanceClause {
	pub name: Option<Value<String>>,
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(deny_unknown_fields)]
pub struct OrganizationClause {}

pub fn match_area_against_filter(_area: &AreaDescriptor, _filter: &AreaClause) -> bool {
	true
}

pub fn match_course_against_filter(_course: &CourseInstance, _filter: &CourseClause) -> Option<MatchedParts> {
	Some(MatchedParts::blank())
}
