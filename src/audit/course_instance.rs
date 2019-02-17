use super::course_match::{MatchType, MatchedCourseParts};
use crate::filter::Clause as Filter;
use crate::rules::course::Rule as CourseRule;
use crate::student::Term;

#[derive(Hash, PartialEq, Eq, Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct CourseInstance {
	pub course: String,
	pub term: Term,
	pub attributes: Vec<String>,
	pub course_type: String,
	pub gereqs: Vec<String>,
	pub section: Option<String>,
	pub subjects: Vec<String>,
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

		let year = match (&self.term.year, &filter.year) {
			(a, Some(b)) if a == b => MatchType::Match(*a),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let semester = match (&self.term.semester, &filter.semester) {
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
			year,
			semester,
			course_type,
			subjects: MatchType::Skip,
			attributes: MatchType::Skip,
			gereqs: MatchType::Skip,
		}
	}

	#[allow(dead_code)]
	pub fn matches_filter(&self, filter: &Filter) -> MatchedCourseParts {
		let section = match (&self.section, filter.get("section")) {
			(Some(a), Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(None, _) | (_, None) => MatchType::Skip,
		};

		let year = match (&self.term.year, filter.get("year")) {
			(a, Some(b)) if &(*a as u64) == b => MatchType::Match(*a),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let semester = match (&self.term.semester, filter.get("semester")) {
			(a, Some(b)) if &a.to_string() == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let course_type = match (&self.course_type, filter.get("type")) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let gereqs = filter
			.get("gereqs")
			.map_or(MatchType::Skip, |gereqs| gereqs.compare_to_slice(&self.gereqs));

		let attributes = filter
			.get("attributes")
			.map_or(MatchType::Skip, |attrs| attrs.compare_to_slice(&self.attributes));

		let subjects = filter
			.get("subjects")
			.map_or(MatchType::Skip, |subjects| subjects.compare_to_slice(&self.subjects));

		MatchedCourseParts {
			course: MatchType::Skip,
			subjects,
			section,
			year,
			semester,
			course_type,
			attributes,
			gereqs,
		}
	}
}
