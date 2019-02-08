use super::course_match::{MatchType, MatchedCourseParts};

#[derive(Hash, PartialEq, Eq, Debug, Clone)]
pub struct CourseInstance {
	course: String,
	department: String,
	section: String,
	term: String,
	year: u64,
	semester: String,
	gereqs: Vec<String>,
	attributes: Vec<String>,
	course_type: String,
}

impl CourseInstance {
	pub fn matches_filter(&self, filter: &crate::rules::course::Rule) -> MatchedCourseParts {
		let course = match (&self.course, &filter.course) {
			(a, b) if a == b => MatchType::Match(a.clone()),
			_ => MatchType::Fail,
		};

		let section = match (&self.section, &filter.section) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
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
