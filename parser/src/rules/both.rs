use crate::rules::Rule as AnyRule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
	pub both: (Box<AnyRule>, Box<AnyRule>),
}

impl crate::rules::traits::PrettyPrint for Rule {
	fn print(&self) -> Result<String, std::fmt::Error> {
		use crate::rules::Rule::{Course, Requirement};
		use std::fmt::Write;

		let mut output = String::new();

		let pair = self.both.clone();

		#[cfg_attr(rustfmt, rustfmt_skip)]
        match (*pair.0, *pair.1) {
            (Requirement(a), Requirement(b)) => {
                write!(&mut output, "complete both the {} and {} requirements", a.print()?, b.print()?)?;
            },
            (Course(a), Course(b)) => {
                write!(&mut output, "take both {} and {}", a.print()?, b.print()?)?;
            },
            (Requirement(a), Course(b)) => {
                write!(&mut output, "take {} and complete the {} requirement", a.print()?, b.print()?)?;
            },
            (Course(a), Requirement(b)) => {
                write!(&mut output, "complete the {} requirement and take {}", a.print()?, b.print()?)?;
            },
            (Course(a), b) => {
                write!(&mut output, "both take {} and [do] {}", a.print()?, b.print()?)?;
            },
            (Requirement(a), b) => {
                write!(&mut output, "both complete the {} requirement and [do] {}", a.print()?, b.print()?)?;
            },
            (a, Course(b)) => {
                write!(&mut output, "both [do] {} and take {}", a.print()?, b.print()?)?;
            },
            (a, Requirement(b)) => {
                write!(&mut output, "both [do] {} and complete the {} requirement", a.print()?, b.print()?)?;
            },
            (a, b) => {
                write!(&mut output, "both {} and {}", a.print()?, b.print()?)?;
            },
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
}
