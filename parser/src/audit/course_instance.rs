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

		// match (&self.gereqs, filter.get("gereqs")) {
		// 	(a, Some(b)) => match (a, b) {
		// 		(WrappedValue::Or(needed), WrappedValue::Or(available)) => {
		// 			// needed.
		// 			// for tag in set {
		// 			// 	match tag {
		// 			// 		TaggedValue::EqualTo(v) => match v {
		// 			// 			Value::String(gereq) => b.contains(gereq),
		// 			// 		},
		// 			// 	}
		// 			// }
		// 			// let possibilities: HashSet<_> = set.iter().collect();
		// 			// possibilities.intersection(a.iter().collect());
		// 			// let matches = Vec::new();
		// 			// for possibility in set {
		// 			// 	for present in a {

		// 			// 	}
		// 			// }
		// 			// let matches = set
		// 			// 	.iter()
		// 			// 	.map(|gereq| {
		// 			// 		if gereq == a {
		// 			// 			MatchType::Match(a.clone())
		// 			// 		} else {
		// 			// 			MatchType::Skip
		// 			// 		}
		// 			// 	})
		// 			// 	.collect::<Vec<_>>();
		// 			// matches.iter().any(|m| )
		// 		}
		// 	},
		// 	// (_, Some(_)) => MatchType::Fail,
		// 	// (_, None) => MatchType::Skip,
		// 	_ => unimplemented!(),
		// };

		// TODO: check subjects/departments
		// TODO: check attributes
		// TODO: check gereqs

		MatchedCourseParts {
			course: MatchType::Skip,
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
