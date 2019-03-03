use super::{Term, Semester};
use crate::grade::Grade;
use decorum::R32;
use serde::{Deserialize, Serialize, de::Deserializer};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CourseInstance {
	pub course: String,
	pub r#type: CourseType,
	pub subjects: Vec<String>,
	pub number: u64,
	pub section: Option<String>,
	pub grade: GradeOption,
	#[serde(deserialize_with = "crate::util::string_or_struct_parseerror")]
	pub term: Term,
	#[serde(deserialize_with = "float_to_decorum")]
	pub credits: R32,
	#[serde(default)]
	pub gereqs: Vec<String>,
	#[serde(default)]
	pub attributes: Vec<String>,
	pub name: String,
}

pub fn float_to_decorum<'de, D>(deserializer: D) -> Result<R32, D::Error>
where
	D: Deserializer<'de>,
{
	let v = f32::deserialize(deserializer)?;
	Ok(R32::from(v))
}

impl CourseInstance {
	pub fn with_course(c: &str) -> CourseInstance {
		CourseInstance {
			course: c.to_string(),
			r#type: CourseType::Research,
			subjects: vec![],
			number: 0,
			section: None,
			grade: GradeOption::NoGrade,
			term: Term {year: 2000, semester: Semester::Fall},
			credits: R32::from(0.0),
			gereqs: vec![],
			attributes: vec![],
			name: "".to_string(),
		}
	}
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[serde(rename_all = "kebab-case")]
pub enum CourseType {
	Research,
	Topic,
	Seminar,
	Lab,
	Flac,
}

/// If the `Option` here is `None`, then the course is in-progress
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[serde(rename_all = "kebab-case", tag = "mode")]
pub enum GradeOption {
	Graded { grade: Option<Grade> },
	Audit { passed: Option<bool> },
	Pn { passed: Option<bool> },
	Su { passed: Option<bool> },
	NoGrade,
}

impl CourseInstance {
	pub fn failed(&self) -> bool {
		match &self.grade {
			GradeOption::Graded { grade } => {
				if let Some(grade) = grade {
					grade <= &Grade::F
				} else {
					false
				}
			}
			GradeOption::Audit { passed } | GradeOption::Pn { passed } | GradeOption::Su { passed } => {
				if let Some(passed) = passed {
					*passed
				} else {
					false
				}
			}
			// TODO: ask around to find out what a NoGrade gradeopt actually means
			GradeOption::NoGrade => false,
		}
	}
}
