use crate::audit::course_match::MatchedParts;
use crate::student::AreaDescriptor;
use crate::student::CourseInstance;
use crate::value::WrappedValue;
use std::collections::BTreeMap;

mod constant;
mod deserialize;
mod print;
#[cfg(test)]
mod tests;

pub(crate) use deserialize::{deserialize_with, deserialize_with_no_option};

pub type Clause = BTreeMap<String, WrappedValue>;

pub fn match_area_against_filter(_area: &AreaDescriptor, _filter: &Clause) -> bool {
	true
}

pub fn match_course_against_filter(_course: &CourseInstance, _filter: &Clause) -> Option<MatchedParts> {
	Some(MatchedParts::blank())
}
