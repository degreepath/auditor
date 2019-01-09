use crate::rules::Rule;
use crate::save::SaveBlock;
use crate::util;
use std::collections::HashMap;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Requirement {
    pub message: Option<String>,
    #[serde(default = "util::serde_false")]
    pub department_audited: bool,
    pub result: Option<Rule>,
    #[serde(default = "util::serde_false")]
    pub contract: bool,
    #[serde(default)]
    pub save: Vec<SaveBlock>,
    #[serde(default)]
    pub requirements: HashMap<String, Requirement>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rules::requirement;

    #[test]
    fn serialize() {
        let data = Requirement {
            message: None,
            department_audited: false,
            result: Some(Rule::Requirement(requirement::RequirementRule {
                requirement: String::from("name"),
                optional: false,
            })),
            contract: false,
            save: vec![],
            requirements: HashMap::new(),
        };

        let expected = "---
message: ~
department_audited: false
result:
  requirement: name
  optional: false
contract: false
save: []
requirements: {}";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize() {
        let data = "---
message: ~
epartment_audited: false
result:
  requirement: name
  optional: false
contract: false
save: []
requirements: {}";

        let expected = Requirement {
            message: None,
            department_audited: false,
            result: Some(Rule::Requirement(requirement::RequirementRule {
                requirement: String::from("name"),
                optional: false,
            })),
            contract: false,
            save: vec![],
            requirements: HashMap::new(),
        };

        let actual: Requirement = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_with_defaults() {
        let data = "---
message: ~
result: {requirement: name, optional: false}";

        let expected = Requirement {
            message: None,
            department_audited: false,
            result: Some(Rule::Requirement(requirement::RequirementRule {
                requirement: String::from("name"),
                optional: false,
            })),
            contract: false,
            save: vec![],
            requirements: HashMap::new(),
        };

        let actual: Requirement = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_message_only() {
        let data = "---
message: a message";

        let expected = Requirement {
            message: Some("a message".to_string()),
            department_audited: false,
            result: None,
            contract: false,
            save: vec![],
            requirements: HashMap::new(),
        };

        let actual: Requirement = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }
}
