use crate::student::Semester;

/// MatchedCourseParts reflects the _course_, not the matching rule or filter.
/// That is, its values are those that _were matched_ from the course.
#[derive(Hash, PartialEq, Eq, Debug, Clone)]
pub struct MatchedCourseParts {
	pub course: MatchType<String>,
	pub year: MatchType<u16>,
	pub semester: MatchType<Semester>,
	pub subjects: MatchType<Vec<MatchType<String>>>,
	pub section: MatchType<String>,
	pub course_type: MatchType<String>,
	pub gereqs: MatchType<Vec<MatchType<String>>>,
	pub attributes: MatchType<Vec<MatchType<String>>>,
}

#[allow(dead_code)]
impl MatchedCourseParts {
	pub fn blank() -> MatchedCourseParts {
		MatchedCourseParts {
			course: MatchType::Skip,
			subjects: MatchType::Skip,
			section: MatchType::Skip,
			year: MatchType::Skip,
			semester: MatchType::Skip,
			course_type: MatchType::Skip,
			gereqs: MatchType::Skip,
			attributes: MatchType::Skip,
		}
	}

	pub fn any(&self) -> bool {
		self.course.matched()
			|| self.section.matched()
			|| self.year.matched()
			|| self.semester.matched()
			|| self.course_type.matched()
			|| self.gereqs.matched()
			|| self.attributes.matched()
	}

	pub fn all(&self) -> bool {
		self.course.matched()
			&& self.section.matched()
			&& self.year.matched()
			&& self.semester.matched()
			&& self.course_type.matched()
			&& self.gereqs.matched()
			&& self.attributes.matched()
	}
}

#[derive(Hash, PartialEq, Eq, Debug, Clone)]
pub enum MatchType<T> {
	Match(T),
	Skip,
	Fail,
}

impl<T> MatchType<T> {
	pub fn matched(&self) -> bool {
		match &self {
			MatchType::Match(_) => true,
			_ => false,
		}
	}

	#[allow(dead_code)]
	pub fn skipped(&self) -> bool {
		match &self {
			MatchType::Skip => true,
			_ => false,
		}
	}

	#[allow(dead_code)]
	pub fn failed(&self) -> bool {
		match &self {
			MatchType::Fail => true,
			_ => false,
		}
	}
}
