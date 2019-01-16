use crate::rules::traits::RuleTools;
use crate::rules::Rule as AnyRule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Rule {
	pub both: (Box<AnyRule>, Box<AnyRule>),
}

impl crate::rules::traits::RuleTools for Rule {
	fn has_save_rule(&self) -> bool {
		self.both.0.has_save_rule() || self.both.1.has_save_rule()
	}
}

impl crate::rules::traits::PrettyPrint for Rule {
	fn print(&self) -> Result<String, std::fmt::Error> {
		use crate::rules::Rule::{Course, Requirement};
		use std::fmt::Write;

		let mut output = String::new();

		let pair = self.both.clone();

		if self.has_save_rule() {
			write!(&mut output, "do both of the following:\n\n")?;
			writeln!(&mut output, "- {}", (*pair.0).print()?)?;
			writeln!(&mut output, "- {}", (*pair.1).print()?)?;
			return Ok(output);
		}

		match (*pair.0, *pair.1) {
			(Requirement(a), Requirement(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "complete both the {} and {} requirements", a.print()?, b.print()?)?;
			}
			(Course(a), Course(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "take both {} and {}", a.print()?, b.print()?)?;
			}
			(Requirement(a), Course(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "complete the {} requirement and take {}", a.print()?, b.print()?)?;
			}
			(Course(a), Requirement(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "take {} and complete the {} requirement", a.print()?, b.print()?)?;
			}
			(Course(a), b) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "both take {} and {}", a.print()?, b.print()?)?;
			}
			(Requirement(a), b) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "both complete the {} requirement and {}", a.print()?, b.print()?)?;
			}
			(a, Course(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "both {} and take {}", a.print()?, b.print()?)?;
			}
			(a, Requirement(b)) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "both {} and complete the {} requirement", a.print()?, b.print()?)?;
			}
			(a, b) => {
				#[cfg_attr(rustfmt, rustfmt_skip)]
				write!(&mut output, "both {} and {}", a.print()?, b.print()?)?;
			}
		};

		Ok(output)
	}
}

#[cfg(test)]
mod tests {
	use super::*;
	use crate::rules::{requirement, Rule as AnyRule};

	#[test]
	fn serialize() {
		let input = Rule {
			both: (
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
both:
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
both:
  - requirement: Name
    optional: false
  - requirement: Name 2
    optional: false";

		let expected_struct = Rule {
			both: (
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

		let input: Rule = serde_yaml::from_str(&"{both: [{requirement: A}, {requirement: B}]}").unwrap();
		let expected = "complete both the “A” and “B” requirements";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{both: [CS 111, CS 121]}").unwrap();
		let expected = "take both CS 111 and CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{both: [CS 121, {requirement: A}]}").unwrap();
		let expected = "take CS 121 and complete the “A” requirement";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{both: [{requirement: A}, CS 121]}").unwrap();
		let expected = "complete the “A” requirement and take CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{both: [CS 121, {both: [CS 251, CS 130]}]}").unwrap();
		let expected = "both take CS 121 and take both CS 251 and CS 130";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{both: [{requirement: A}, {both: [CS 251, CS 130]}]}").unwrap();
		let expected = "both complete the “A” requirement and take both CS 251 and CS 130";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{both: [{given: courses, what: courses, do: count >= 3}, CS 121]}").unwrap();
		let expected = "both take at least three courses and take CS 121";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule =
			serde_yaml::from_str(&"{both: [{given: courses, what: courses, do: count >= 3}, {requirement: A}]}")
				.unwrap();
		let expected = "both take at least three courses and complete the “A” requirement";
		assert_eq!(expected, input.print().unwrap());

		let input: Rule = serde_yaml::from_str(&"{both: [{given: courses, what: courses, do: count >= 3}, {given: these courses, courses: [THEAT 233], repeats: all, what: courses, do: count >= 4}]}").unwrap();
		let expected = "both take at least three courses and take THEAT 233 at least four times";
		assert_eq!(expected, input.print().unwrap());
	}
}
