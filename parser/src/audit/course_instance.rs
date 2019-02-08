use super::course_match::{MatchType, MatchedCourseParts};
// use crate::filter::Clause as Filter;
use crate::rules::course::Rule as CourseRule;

#[derive(Hash, PartialEq, Eq, Debug, Clone)]
pub struct CourseInstance {
	pub attributes: Vec<String>,
	pub course_type: String,
	pub course: String,
	pub gereqs: Vec<String>,
	pub section: Option<String>,
	pub semester: String,
	pub subjects: Vec<String>,
	pub term: String,
	pub year: u64,
}

impl CourseInstance {
	pub fn matches_rule(&self, filter: &CourseRule) -> MatchedCourseParts {
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

		// TODO: check subjects/departments
		// TODO: check attributes
		// TODO: check gereqs

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
