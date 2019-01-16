use crate::rules::traits::RuleTools;
use crate::rules::Rule as AnyRule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub either: (Box<AnyRule>, Box<AnyRule>),
}

impl crate::rules::traits::RuleTools for Rule {
	fn has_save_rule(&self) -> bool {
		self.either.0.has_save_rule() || self.either.1.has_save_rule()
	}
}

impl crate::rules::traits::PrettyPrint for Rule {
	fn print(&self) -> Result<String, std::fmt::Error> {
		use crate::rules::Rule::{Course, Requirement};
		use std::fmt::Write;

		let mut output = String::new();

		let pair = self.either.clone();

		if self.has_save_rule() {
			write!(&mut output, "do both of the following:\n\n")?;
			writeln!(&mut output, "- {}", (*pair.0).print()?)?;
			writeln!(&mut output, "- {}", (*pair.1).print()?)?;
			return Ok(output);
		}

		match (*pair.0, *pair.1) {
			(Requirement(a), Requirement(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "complete either the {} or {} requirement", a.print()?, b.print()?)?;
			}
			(Course(a), Course(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "take either {} or {}", a.print()?, b.print()?)?;
			}
			(Requirement(a), Course(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "complete the {} requirement or take {}", a.print()?, b.print()?)?;
			}
			(Course(a), Requirement(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "take {} or complete the {} requirement", a.print()?, b.print()?)?;
			}
			(Course(a), b) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "either take {} or {}", a.print()?, b.print()?)?;
			}
			(Requirement(a), b) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "either complete the {} requirement or {}", a.print()?, b.print()?)?;
			}
			(a, Course(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "either {} or take {}", a.print()?, b.print()?)?;
			}
			(a, Requirement(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "either {} or complete the {} requirement", a.print()?, b.print()?)?;
			}
			(a, b) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "either {} or {}", a.print()?, b.print()?)?;
			}
		};

		Ok(output)
	}
}

#[cfg(test)]
mod tests {
	use super::*;
	use crate::rules::requirement;

	#[test]
	fn serialize() {
		let input = Rule {
			either: (
				Box::new(AnyRule::Requirement(requirement::Rule {
					requirement: String::from("Name"),
					optional: false,
				})),
				Box::new(AnyRule::Requirement(requirement::Rule {
					requirement: String::from("Name 2"),
					optional: false,
				})),
			),
		};

		let expected_str = "---
either:
  - requirement: Name
    optional: false
  - requirement: Name 2
    optional: false";

		let actual = serde_yaml::to_string(&input).unwrap();
		assert_eq!(actual, expected_str);
	}

	#[test]
	fn deserialize() {
		let input = "---
either:
  - requirement: Name
    optional: false
  - requirement: Name 2
    optional: false";

		let expected_struct = Rule {
			either: (
				Box::new(AnyRule::Requirement(requirement::Rule {
					requirement: String::from("Name"),
					optional: false,
				})),
				Box::new(AnyRule::Requirement(requirement::Rule {
					requirement: String::from("Name 2"),
					optional: false,
				})),
			),
		};

		let actual: Rule = serde_yaml::from_str(&input).unwrap();
		assert_eq!(actual, expected_struct);
	}

	#[test]
	fn pretty_print() {
		use crate::rules::traits::PrettyPrint;

		let input: Rule = serde_yaml::from_str(&"{either: [{requirement: A}, {requirement: B}]}").unwrap();
		let expected = "complete either the “A” or “B” requirement";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{either: [CS 111, CS 121]}").unwrap();
		let expected = "take either CS 111 or CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{either: [CS 121, {requirement: A}]}").unwrap();
		let expected = "take CS 121 or complete the “A” requirement";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{either: [{requirement: A}, CS 121]}").unwrap();
		let expected = "complete the “A” requirement or take CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{either: [CS 121, {either: [CS 251, CS 130]}]}").unwrap();
		let expected = "either take CS 121 or take either CS 251 or CS 130";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{either: [{requirement: A}, {either: [CS 251, CS 130]}]}").unwrap();
		let expected = "either complete the “A” requirement or take either CS 251 or CS 130";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{either: [{given: courses, what: courses, do: count >= 3}, CS 121]}").unwrap();
		let expected = "either take at least three courses or take CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{either: [{given: courses, what: courses, do: count >= 3}, {requirement: A}]}")
				.unwrap();
		let expected = "either take at least three courses or complete the “A” requirement";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{either: [{given: courses, what: courses, do: count >= 3}, {given: these courses, courses: [THEAT 233], repeats: all, what: courses, do: count >= 4}]}").unwrap();
		let expected = "either take at least three courses or take THEAT 233 at least four times";
		assert_eq!(expected, input.print().unwrap());
	}
}
