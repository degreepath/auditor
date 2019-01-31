pub mod action_only;
pub mod both;
pub mod count_of;
pub mod course;
pub mod either;
pub mod given;
pub mod req_ref;

use crate::traits::{audit, print, Util};
use crate::util;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Rule {
	Course(#[serde(deserialize_with = "util::string_or_struct")] course::Rule),
	Requirement(req_ref::Rule),
	CountOf(count_of::Rule),
	Both(both::Rule),
	Either(either::Rule),
	Given(given::Rule),
	Do(action_only::Rule),
}

impl print::Print for Rule {
	fn print(&self) -> print::Result {
		match &self {
			Rule::Course(v) => Ok(format!("take {}", v.print()?)),
			Rule::Requirement(v) => Ok(format!("complete the {} requirement", v.print()?)),
			Rule::CountOf(v) => v.print(),
			Rule::Both(v) => v.print(),
			Rule::Either(v) => v.print(),
			Rule::Given(v) => v.print(),
			Rule::Do(v) => v.print(),
		}
	}
}

impl Util for Rule {
	fn has_save_rule(&self) -> bool {
		match &self {
			Rule::Course(v) => v.has_save_rule(),
			Rule::Requirement(v) => v.has_save_rule(),
			Rule::CountOf(v) => v.has_save_rule(),
			Rule::Both(v) => v.has_save_rule(),
			Rule::Either(v) => v.has_save_rule(),
			Rule::Given(v) => v.has_save_rule(),
			Rule::Do(v) => v.has_save_rule(),
		}
	}
}

impl audit::rule::Audit for Rule {
	fn check(&self, state: &audit::AuditState) -> audit::rule::RuleState {
		match &self {
			Rule::Course(v) => v.check(state),
			// Rule::Requirement(v) => v.check(state),
			// Rule::CountOf(v) => v.check(state),
			// Rule::Both(v) => v.check(state),
			Rule::Either(v) => v.check(state),
			// Rule::Given(v) => v.check(state),
			// Rule::Do(v) => v.check(state),
			_ => unimplemented!("auditing is in-progress"),
		}
	}
}
impl Rule {
	fn print_inner(&self) -> print::Result {
		use crate::traits::print::Print;

		match &self {
			Rule::Course(v) => v.print(),
			Rule::Requirement(v) => v.print(),
			Rule::CountOf(v) => v.print(),
			Rule::Both(v) => v.print(),
			Rule::Either(v) => v.print(),
			Rule::Given(v) => v.print(),
			Rule::Do(v) => v.print(),
		}
	}
}
