pub mod action_only;
pub mod both;
pub mod count_of;
pub mod course;
pub mod either;
pub mod given;
pub mod req_ref;

use serde::{Deserialize, Serialize};

use crate::traits::{print, Util};

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Clone)]
#[serde(tag = "type", rename_all = "kebab-case")]
pub enum Rule {
	Course(course::Rule),
	Requirement(req_ref::Rule),
	CountOf(count_of::Rule),
	Both(both::Rule),
	Either(either::Rule),
	Given(given::Rule),
	Do(action_only::Rule),
}

impl<'de> Deserialize<'de> for Rule {
	fn deserialize<D>(deserializer: D) -> Result<Rule, D::Error>
	where
		D: serde::de::Deserializer<'de>,
	{
		string_or_rule(deserializer)
	}
}

pub fn string_or_rule<'de, D>(deserializer: D) -> Result<Rule, D::Error>
where
	D: serde::de::Deserializer<'de>,
{
	use serde::de::{self, MapAccess, Visitor};
	use std::fmt;
	pub struct RuleVisitor;

	impl<'de> Visitor<'de> for RuleVisitor {
		type Value = Rule;

		fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
			formatter.write_str("string or map")
		}

		fn visit_str<E>(self, value: &str) -> Result<Rule, E>
		where
			E: de::Error,
		{
			let course: course::Rule = value.parse().unwrap();
			Ok(Rule::Course(course))
		}

		fn visit_map<M>(self, map: M) -> Result<Rule, M::Error>
		where
			M: MapAccess<'de>,
		{
			#[derive(Deserialize)]
			#[serde(remote = "Rule")]
			#[serde(tag = "type", rename_all = "kebab-case")]
			enum RuleHelper {
				Course(course::Rule),
				Requirement(req_ref::Rule),
				CountOf(count_of::Rule),
				Both(both::Rule),
				Either(either::Rule),
				Given(given::Rule),
				Do(action_only::Rule),
			}

			RuleHelper::deserialize(de::value::MapAccessDeserializer::new(map))
		}
	}

	deserializer.deserialize_any(RuleVisitor {})
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
