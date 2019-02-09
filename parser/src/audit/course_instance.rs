use super::course_match::{MatchType, MatchedCourseParts};
use crate::filter::{Clause as Filter, TaggedValue, Value, WrappedValue};
use crate::rules::course::Rule as CourseRule;
use std::collections::HashSet;

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

		MatchedCourseParts {
			course,
			section,
			term,
			year,
			semester,
			course_type,
			subjects: MatchType::Skip,
			attributes: MatchType::Skip,
			gereqs: MatchType::Skip,
		}
	}

	pub fn matches_filter(&self, filter: &Filter) -> MatchedCourseParts {
		let section = match (&self.section, filter.get("section")) {
			(Some(a), Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(None, _) | (_, None) => MatchType::Skip,
		};

		let term = match (&self.term, filter.get("term")) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let year = match (&self.year, filter.get("year")) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
			(_, Some(_)) => MatchType::Fail,
			(_, None) => MatchType::Skip,
		};

		let semester = match (&self.semester, filter.get("semester")) {
			(a, Some(b)) if a == b => MatchType::Match(a.clone()),
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
			term,
			year,
			semester,
			course_type,
			attributes,
			gereqs,
		}
	}
}
