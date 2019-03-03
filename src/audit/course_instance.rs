use super::course_match::{MatchType, MatchedParts};
use crate::filter::CourseClause;
use crate::filterable_data::DataValue as Val;
use crate::rules::course::Rule as CourseRule;
use crate::student::CourseInstance;
use std::collections::BTreeMap;

impl CourseInstance {
	pub fn matches_rule(&self, filter: &CourseRule) -> MatchedParts {
		let mut result: BTreeMap<String, MatchType<Val>> = BTreeMap::new();

		if self.course == filter.course {
			result.insert("course".to_owned(), MatchType::Match(self.course.clone().into()));
		}

		// .filter_map(|(k{ey, value)| match key.as_ref() {
		// 	"course" => Some((
		// 		key.clone(),
		// 		if value == &filter.course {
		// 			MatchType::Match(value.clone())
		// 		} else {
		// 			MatchType::Fail
		// 		},
		// 	)),
		// 	"section" => Some((
		// 		key.clone(),
		// 		match &filter.section {
		// 			Some(section) if value == section => MatchType::Match(value.clone()),
		// 			Some(_) => MatchType::Fail,
		// 			None => MatchType::Skip,
		// 		},
		// 	)),
		// 	"year" => Some((
		// 		key.clone(),
		// 		match &filter.year {
		// 			Some(year) if value == year => MatchType::Match(value.clone()),
		// 			Some(_) => MatchType::Fail,
		// 			None => MatchType::Skip,
		// 		},
		// 	)),
		// 	"semester" => Some((
		// 		key.clone(),
		// 		match &filter.semester {
		// 			Some(semester) if *value == semester.to_string() => MatchType::Match(value.clone()),
		// 			Some(_) => MatchType::Fail,
		// 			None => MatchType::Skip,
		// 		},
		// 	)),
		// 	"type" => Some((
		// 		key.clone(),
		// 		match &filter.lab {
		// 			Some(only_labs) if value == "Lab" && *only_labs == true => MatchType::Match(value.clone()),
		// 			Some(_) => MatchType::Fail,
		// 			None => MatchType::Skip,
		// 		},
		// 	)),
		// 	_ => None,
		// })
		// .collect();}

		MatchedParts::new(&result)
	}

	#[allow(dead_code)]
	pub fn matches_filter(&self, filter: &CourseClause) -> MatchedParts {
		let result: BTreeMap<String, MatchType<Val>> = BTreeMap::new();
		// self
		// .iter()
		// .map(|(key, value)| {
		// 	(
		// 		key.clone(),
		// 		match filter.get(key) {
		// 			Some(other_val) => match &value {
		// 				Val::String(_) | Val::Integer(_) | Val::Float(_) | Val::Boolean(_) => {
		// 					if value == other_val {
		// 						MatchType::Match(value.clone())
		// 					} else {
		// 						MatchType::Fail
		// 					}
		// 				}
		// 				// Val::Vec(slice) => MatchType::Match(Val::Vec(other_val.compare_to_slice(slice))),
		// 				Val::Vec(_) => unimplemented!("'vec' filterable values"),
		// 				Val::Map(_) => unimplemented!("'map' filterable values"),
		// 				Val::DateTime(_) => unimplemented!("'datetime' filterable values"),
		// 			},
		// 			None => MatchType::Skip,
		// 		},
		// 	)
		// })
		// .collect();

		MatchedParts::new(&result)
	}
}
