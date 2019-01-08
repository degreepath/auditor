use crate::rules::Rule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct BothRule {
    pub both: (Box<Rule>, Box<Rule>),
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rules::{requirement, Rule};

    #[test]
    fn serialize() {
        let input = BothRule {
            both: (
                Box::new(Rule::Requirement(requirement::RequirementRule {
                    requirement: String::from("Name"),
                    optional: false,
                })),
                Box::new(Rule::Requirement(requirement::RequirementRule {
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
        
        let expected_struct = BothRule {
            both: (
                Box::new(Rule::Requirement(requirement::RequirementRule {
                    requirement: String::from("Name"),
                    optional: false,
                })),
                Box::new(Rule::Requirement(requirement::RequirementRule {
                    requirement: String::from("Name 2"),
                    optional: false,
                })),
            ),
        };


        let actual: BothRule = serde_yaml::from_str(&input).unwrap();
        assert_eq!(actual, expected_struct);
    }
}
