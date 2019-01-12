use crate::rules::Rule as AnyRule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    pub both: (Box<AnyRule>, Box<AnyRule>),
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
