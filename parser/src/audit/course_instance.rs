use super::course_match::{MatchType, MatchedCourseParts};

#[derive(Hash, PartialEq, Eq, Debug, Clone)]
pub struct CourseInstance {
	pub course: String,
	pub department: String,
	pub section: Option<String>,
	pub term: String,
	pub year: u64,
	pub semester: String,
	pub gereqs: Vec<String>,
	pub attributes: Vec<String>,
	pub course_type: String,
}

impl CourseInstance {
	pub fn matches_filter(&self, filter: &crate::rules::course::Rule) -> MatchedCourseParts {
		let course = match (&self.course, &filter.course) {
			(a, b) if a == b => MatchType::Match(a.clone()),
			_ => MatchType::Fail,
		};

		let section = match (&self.section, &filter.section) {
			(Some(a), Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(None, _) => MatchType::Skip,
			(_, None) => MatchType::Skip,
		};

		let term = match (&self.term, &filter.term) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let year = match (&self.year, &filter.year) {
			(a, Some(b)) if a == b => MatchType::Match(*a),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let semester = match (&self.semester, &filter.semester) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let course_type = match (&self.course_type, &filter.lab) {
			(a, Some(b)) if *b == true && a == "Lab" => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		MatchedCourseParts {
			course,
			section,
			term,
			year,
			semester,
			course_type,
			attributes: MatchType::Skip,
			gereqs: MatchType::Skip,
		}
	}
}
