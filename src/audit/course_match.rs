use crate::grade::Grade;
use crate::student::{CourseType, Semester};
use decorum::R32;
use serde::{Deserialize, Serialize};

/// MatchedCourseParts reflects the _course_, not the matching rule or filter.
/// That is, its values are those that _were matched_ from the course.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct MatchedParts {
	pub attribute: MatchType<Vec<MatchType<String>>>,
	pub course: MatchType<String>,
	pub credits: MatchType<R32>,
	pub gereqs: MatchType<Vec<MatchType<String>>>,
	pub grade: MatchType<Grade>,
	pub graded: MatchType<bool>,
	pub institution: MatchType<String>,
	pub level: MatchType<u64>,
	pub number: MatchType<u64>,
	pub section: MatchType<String>,
	pub semester: MatchType<Semester>,
	pub subject: MatchType<Vec<MatchType<String>>>,
	pub r#type: MatchType<CourseType>,
	pub year: MatchType<u16>,
}

#[allow(dead_code)]
impl MatchedParts {
	pub fn any_match(&self) -> bool {
		self.attribute.is_match()
			|| self.course.is_match()
			|| self.credits.is_match()
			|| self.gereqs.is_match()
			|| self.grade.is_match()
			|| self.graded.is_match()
			|| self.institution.is_match()
			|| self.number.is_match()
			|| self.section.is_match()
			|| self.semester.is_match()
			|| self.subject.is_match()
			|| self.r#type.is_match()
			|| self.year.is_match()
	}

	pub fn all_match(&self) -> bool {
		self.attribute.is_match()
			&& self.course.is_match()
			&& self.credits.is_match()
			&& self.gereqs.is_match()
			&& self.grade.is_match()
			&& self.graded.is_match()
			&& self.institution.is_match()
			&& self.number.is_match()
			&& self.section.is_match()
			&& self.semester.is_match()
			&& self.subject.is_match()
			&& self.r#type.is_match()
			&& self.year.is_match()
	}
}

impl std::default::Default for MatchedParts {
	fn default() -> Self {
		MatchedParts {
			attribute: MatchType::default(),
			course: MatchType::default(),
			credits: MatchType::default(),
			gereqs: MatchType::default(),
			grade: MatchType::default(),
			graded: MatchType::default(),
			institution: MatchType::default(),
			level: MatchType::default(),
			number: MatchType::default(),
			semester: MatchType::default(),
			section: MatchType::default(),
			subject: MatchType::default(),
			r#type: MatchType::default(),
			year: MatchType::default(),
		}
	}
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum MatchType<T> {
	Match(T),
	Skip,
	Fail,
}

impl<T> std::default::Default for MatchType<T> {
	fn default() -> Self {
		MatchType::Skip
	}
}

impl<T> MatchType<T> {
	pub fn is_match(&self) -> bool {
		match &self {
			MatchType::Match(_) => true,
			_ => false,
		}
	}

	#[allow(dead_code)]
	pub fn is_skip(&self) -> bool {
		match &self {
			MatchType::Skip => true,
			_ => false,
		}
	}

	#[allow(dead_code)]
	pub fn is_fail(&self) -> bool {
		match &self {
			MatchType::Fail => true,
			_ => false,
		}
	}
}
