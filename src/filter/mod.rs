use crate::grade::Grade;
use crate::student::{CourseType, Semester};
use crate::value::WrappedValue as Value;
use decorum::R32;
use serde::{Deserialize, Serialize};

mod constant;
mod print;
#[cfg(test)]
mod tests;

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(deny_unknown_fields)]
pub struct CourseClause {
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::string")]
	pub attribute: Option<Value<String>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::string")]
	pub course: Option<Value<String>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::real")]
	pub credits: Option<Value<R32>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::string")]
	pub gereqs: Option<Value<String>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::graded")]
	pub graded: Option<Value<GradeOption>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::grade")]
	pub grade: Option<Value<Grade>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::string")]
	pub institution: Option<Value<String>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::int")]
	pub level: Option<Value<u64>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::int")]
	pub number: Option<Value<u64>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::kind")]
	pub r#type: Option<Value<CourseType>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::semester")]
	pub semester: Option<Value<Semester>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::string")]
	pub subject: Option<Value<String>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::year")]
	pub year: Option<Value<ClassificationYear>>,
}

mod de {
	use crate::value::WrappedValue;
	use serde::{self, Deserialize, Deserializer};

	fn deserialize_parse<'de, D, T>(deserializer: D) -> Result<Option<WrappedValue<T>>, D::Error>
	where
		D: Deserializer<'de>,
		T: std::str::FromStr,
	{
		let o: Option<String> = Option::deserialize(deserializer)?;

		Ok(match o {
			Some(s) => Some(match s.parse::<WrappedValue<T>>() {
				Ok(v) => v,
				Err(e) => panic!("{:?}: {}", e, s),
			}),
			None => None,
		})
	}

	pub fn string<'de, D>(deserializer: D) -> Result<Option<WrappedValue<String>>, D::Error>
	where
		D: Deserializer<'de>,
	{
		deserialize_parse(deserializer)
	}

	pub fn int<'de, D>(deserializer: D) -> Result<Option<WrappedValue<u64>>, D::Error>
	where
		D: Deserializer<'de>,
	{
		deserialize_parse(deserializer)
	}

	pub fn real<'de, D>(deserializer: D) -> Result<Option<WrappedValue<super::R32>>, D::Error>
	where
		D: Deserializer<'de>,
	{
		deserialize_parse(deserializer)
	}

	pub fn semester<'de, D>(deserializer: D) -> Result<Option<WrappedValue<super::Semester>>, D::Error>
	where
		D: Deserializer<'de>,
	{
		deserialize_parse(deserializer)
	}

	pub fn year<'de, D>(deserializer: D) -> Result<Option<WrappedValue<super::ClassificationYear>>, D::Error>
	where
		D: Deserializer<'de>,
	{
		deserialize_parse(deserializer)
	}

	pub fn graded<'de, D>(deserializer: D) -> Result<Option<WrappedValue<super::GradeOption>>, D::Error>
	where
		D: serde::de::Deserializer<'de>,
	{
		// #[derive(Deserialize)]
		// struct Wrapper(WrappedValue<super::GradeOption>);

		// let v = Option::deserialize(deserializer)?;
		// Ok(v.map(|Wrapper(a)| a))
		deserialize_parse(deserializer)
	}

	pub fn grade<'de, D>(deserializer: D) -> Result<Option<WrappedValue<super::Grade>>, D::Error>
	where
		D: serde::de::Deserializer<'de>,
	{
		deserialize_parse(deserializer)
	}

	pub fn kind<'de, D>(deserializer: D) -> Result<Option<WrappedValue<super::CourseType>>, D::Error>
	where
		D: serde::de::Deserializer<'de>,
	{
		#[derive(Deserialize)]
		struct Wrapper(WrappedValue<super::CourseType>);

		let v = Option::deserialize(deserializer)?;
		Ok(v.map(|Wrapper(a)| a))
	}

	pub fn area_type<'de, D>(deserializer: D) -> Result<Option<WrappedValue<super::AreaType>>, D::Error>
	where
		D: serde::de::Deserializer<'de>,
	{
		// #[derive(Deserialize)]
		// struct Wrapper(WrappedValue<super::AreaType>);

		// let v = Option::deserialize(deserializer)?;
		// Ok(v.map(|Wrapper(a)| a))
		deserialize_parse(deserializer)
	}
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

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[serde(rename_all = "kebab-case")]
pub enum GradeOption {
	Graded,
	Audit,
	Pn,
	Su,
	NoGrade,
}

impl std::str::FromStr for GradeOption {
	type Err = crate::util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		use crate::util::ParseError;

		match s.trim() {
			"graded" => Ok(GradeOption::Graded),
			"audit" => Ok(GradeOption::Audit),
			"audited" => Ok(GradeOption::Audit),
			"pn" => Ok(GradeOption::Pn),
			"p/n" => Ok(GradeOption::Pn),
			"su" => Ok(GradeOption::Su),
			"s/u" => Ok(GradeOption::Su),
			"no-grade" => Ok(GradeOption::NoGrade),
			_ => Err(ParseError::InvalidValue),
		}
	}
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(deny_unknown_fields)]
pub struct AreaClause {
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::string")]
	name: Option<Value<String>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::area_type")]
	r#type: Option<Value<AreaType>>,
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd)]
#[serde(rename_all = "lowercase")]
pub enum AreaType {
	Degree,
	Major,
	Minor,
	Concentration,
	Emphasis,
}

impl std::str::FromStr for AreaType {
	type Err = crate::util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		use crate::util::ParseError;

		match s.trim() {
			"degree" => Ok(AreaType::Degree),
			"major" => Ok(AreaType::Major),
			"minor" => Ok(AreaType::Minor),
			"concentration" => Ok(AreaType::Concentration),
			"emphasis" => Ok(AreaType::Emphasis),
			_ => Err(ParseError::InvalidValue),
		}
	}
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
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::string")]
	pub name: Option<Value<String>>,
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::year")]
	pub year: Option<Value<ClassificationYear>>,
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(deny_unknown_fields)]
pub struct AttendanceClause {
	#[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "de::string")]
	pub name: Option<Value<String>>,
}

#[derive(Debug, Serialize, Deserialize, Hash, Clone, PartialEq, Eq, Ord, PartialOrd, Default)]
#[serde(deny_unknown_fields)]
pub struct OrganizationClause {}
