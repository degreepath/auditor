use crate::rules::Rule;
use crate::save::SaveBlock;
use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Requirement {
    pub name: String,
    pub message: Option<String>,
    #[serde(default = "util::serde_false")]
    pub department_audited: bool,
    pub result: Rule,
    #[serde(default = "util::serde_false")]
    pub contract: bool,
    #[serde(default)]
    pub save: Vec<SaveBlock>,
    #[serde(default)]
    pub requirements: Vec<Requirement>,
}

mod tests {
    use super::*;
    use crate::rules::requirement;

    #[test]
    fn serialize() {
        let data = Requirement {
            name: String::from("Name"),
            message: None,
            department_audited: false,
            result: Rule::Requirement(requirement::RequirementRule {
                requirement: String::from("name"),
                optional: false,
            }),
            contract: false,
            save: vec![],
            requirements: vec![],
        };
        let expected = "---
name: Name
message: ~
department_audited: false
result:
  requirement: name
  optional: false
contract: false
save: []
requirements: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize() {
        let data = "---
name: Name
message: ~
epartment_audited: false
result:
  requirement: name
  optional: false
contract: false
save: []
requirements: []";
        let expected = Requirement {
            name: String::from("Name"),
            message: None,
            department_audited: false,
            result: Rule::Requirement(requirement::RequirementRule {
                requirement: String::from("name"),
                optional: false,
            }),
            contract: false,
            save: vec![],
            requirements: vec![],
        };

        let actual: Requirement = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_with_defaults() {
        let data = "---
name: Name
message: ~
result: {requirement: name, optional: false}";
        let expected = Requirement {
            name: String::from("Name"),
            message: None,
            department_audited: false,
            result: Rule::Requirement(requirement::RequirementRule {
                requirement: String::from("name"),
                optional: false,
            }),
            contract: false,
            save: vec![],
            requirements: vec![],
        };

        let actual: Requirement = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }
}
