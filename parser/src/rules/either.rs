use crate::rules::Rule as AnyRule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    pub either: (Box<AnyRule>, Box<AnyRule>),
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
