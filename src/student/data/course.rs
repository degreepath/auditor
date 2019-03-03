use super::{Semester, Term};
use crate::grade::Grade;
use decorum::R32;
use serde::{de::Deserializer, Deserialize, Serialize};

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
			term: Term {
				year: 2000,
				semester: Semester::Fall,
			},
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
#[serde(rename_all = "kebab-case", tag = "graded")]
pub enum GradeOption {
	Graded {
		#[serde(default, skip_serializing_if = "Option::is_none")]
		grade: Option<Grade>,
	},
	Audit {
		#[serde(default, skip_serializing_if = "Option::is_none")]
		passed: Option<bool>,
	},
	Pn {
		#[serde(default, skip_serializing_if = "Option::is_none")]
		passed: Option<bool>,
	},
	Su {
		#[serde(default, skip_serializing_if = "Option::is_none")]
		passed: Option<bool>,
	},
	NoGrade,
}

#[cfg(test)]
mod tests {
	use super::{Grade, GradeOption};
	use insta::assert_yaml_snapshot_matches;

	#[test]
	fn serialize_graded_none() {
		assert_yaml_snapshot_matches!(GradeOption::Graded {grade: None}, @r###"graded: graded"###);
	}

	#[test]
	fn serialize_graded_some() {
		assert_yaml_snapshot_matches!(GradeOption::Graded {grade: Some(Grade::A)}, @r###"graded: graded
grade: A"###);
	}

	#[test]
	fn serialize_audit_none() {
		assert_yaml_snapshot_matches!(GradeOption::Audit {passed: None}, @r###"graded: audit"###);
	}

	#[test]
	fn serialize_audit_some() {
		assert_yaml_snapshot_matches!(GradeOption::Audit {passed: Some(true)}, @r###"graded: audit
passed: true"###);
	}

	#[test]
	fn serialize_pn_none() {
		assert_yaml_snapshot_matches!(GradeOption::Pn {passed: None}, @r###"graded: pn"###);
	}

	#[test]
	fn serialize_pn_some() {
		assert_yaml_snapshot_matches!(GradeOption::Pn {passed: Some(true)}, @r###"graded: pn
passed: true"###);
	}

	#[test]
	fn deserialize_pn_some() {
		let s = "{graded: pn, passed: true}";
		let actual: GradeOption = serde_yaml::from_str(&s).unwrap();
		assert_eq!(actual, GradeOption::Pn { passed: Some(true) });
	}

	#[test]
	fn deserialize_pn_none() {
		let s = "{graded: pn}";
		let actual: GradeOption = serde_yaml::from_str(&s).unwrap();
		assert_eq!(actual, GradeOption::Pn { passed: None });
	}

	#[test]
	fn serialize_su_none() {
		assert_yaml_snapshot_matches!(GradeOption::Su {passed: None}, @r###"graded: su"###);
	}

	#[test]
	fn serialize_su_some() {
		assert_yaml_snapshot_matches!(GradeOption::Su {passed: Some(true)}, @r###"graded: su
passed: true"###);
	}

	#[test]
	fn serialize_nograde_none() {
		assert_yaml_snapshot_matches!(GradeOption::NoGrade, @"graded: no-grade");
	}
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
