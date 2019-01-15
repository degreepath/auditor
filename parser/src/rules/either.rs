use crate::rules::Rule as AnyRule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    pub either: (Box<AnyRule>, Box<AnyRule>),
}

impl crate::rules::traits::PrettyPrint for Rule {
    fn print(&self) -> Result<String, std::fmt::Error> {
        use crate::rules::Rule::{Course, Requirement};
        use std::fmt::Write;

        let mut output = String::new();

        let pair = self.either.clone();

        #[cfg_attr(rustfmt, rustfmt_skip)]
        match (*pair.0, *pair.1) {
            (Requirement(a), Requirement(b)) => {
                write!(&mut output, "complete either the {} or {} requirement", a.print()?, b.print()?)?;
            },
            (Course(a), Course(b)) => {
                write!(&mut output, "take either {} or {}", a.print()?, b.print()?)?;
            },
            (Requirement(a), Course(b)) => {
                write!(&mut output, "take {} or complete the {} requirement", a.print()?, b.print()?)?;
            },
            (Course(a), Requirement(b)) => {
                write!(&mut output, "complete the {} requirement or take {}", a.print()?, b.print()?)?;
            },
            (Course(a), b) => {
                write!(&mut output, "either take {} or [do] {}", a.print()?, b.print()?)?;
            },
            (Requirement(a), b) => {
                write!(&mut output, "either complete the {} requirement or [do] {}", a.print()?, b.print()?)?;
            },
            (a, Course(b)) => {
                write!(&mut output, "either [do] {} or take {}", a.print()?, b.print()?)?;
            },
            (a, Requirement(b)) => {
                write!(&mut output, "either [do] {} or complete the {} requirement", a.print()?, b.print()?)?;
            },
            (a, b) => {
                write!(&mut output, "either {} or {}", a.print()?, b.print()?)?;
            },
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
}
