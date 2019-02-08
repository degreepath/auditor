#[derive(Hash, PartialEq, Eq, Debug, Clone)]
pub struct MatchedCourseParts {
	pub course: MatchType<String>,
	pub section: MatchType<String>,
	pub term: MatchType<String>,
	pub year: MatchType<u64>,
	pub semester: MatchType<String>,
	pub course_type: MatchType<String>,
	pub gereqs: MatchType<Vec<MatchType<String>>>,
	pub attributes: MatchType<Vec<MatchType<String>>>,
}

impl MatchedCourseParts {
	pub fn any(&self) -> bool {
		self.course.matched()
			|| self.section.matched()
			|| self.term.matched()
			|| self.year.matched()
			|| self.semester.matched()
			|| self.course_type.matched()
			|| self.gereqs.matched()
			|| self.attributes.matched()
	}

	pub fn all(&self) -> bool {
		self.course.matched()
			&& self.section.matched()
			&& self.term.matched()
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
