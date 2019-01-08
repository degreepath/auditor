pub mod both;
pub mod count_of;
pub mod course;
pub mod either;
pub mod given;
pub mod requirement;

use crate::util::string_or_struct;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Rule {
    Course(#[serde(deserialize_with = "string_or_struct")] course::CourseRule),
    Requirement(requirement::RequirementRule),
    CountOf(count_of::CountOfRule),
    Both(both::BothRule),
    Either(either::EitherRule),
    Given(given::GivenRule),
}

mod tests {
    use super::*;

    #[test]
    fn serialize() {
        let data = vec![
            Rule::Course(course::CourseRule {
                course: "ASIAN 101".to_string(),
                section: None,
                term: None,
                semester: None,
                year: None,
                international: None,
                lab: None,
            }),
            Rule::Requirement(requirement::RequirementRule {
                requirement: "Name".to_string(),
                optional: true,
            }),
        ];
        let expected = r#"---
- ASIAN 101
- requirement: Name
  optional: true"#;

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);
    }

    // #[test]
    // fn deserialize() {
    //     let data = "---\nname: Name\nmessage: ~\ndepartment_audited: false\nresult:\n  requirement: name\n  optional: false\ncontract: false\nsave: []\nrequirements: []";
    //     let expected = Requirement {
    //         name: String::from("Name"),
    //         message: None,
    //         department_audited: false,
    //         result: Rule::Requirement(requirement::RequirementRule {
    //             requirement: String::from("name"),
    //             optional: false,
    //         }),
    //         contract: false,
    //         save: vec![],
    //         requirements: vec![],
    //     };

    //     let actual: Requirement = serde_yaml::from_str(&data).unwrap();
    //     assert_eq!(actual, expected);
    // }

    // #[test]
    // fn deserialize_with_defaults() {
    //     let data = "---\nname: Name\nmessage: ~\nresult: {requirement: name, optional: false}\n";
    //     let expected = Requirement {
    //         name: String::from("Name"),
    //         message: None,
    //         department_audited: false,
    //         result: Rule::Requirement(requirement::RequirementRule {
    //             requirement: String::from("name"),
    //             optional: false,
    //         }),
    //         contract: false,
    //         save: vec![],
    //         requirements: vec![],
    //     };

    //     let actual: Requirement = serde_yaml::from_str(&data).unwrap();
    //     assert_eq!(actual, expected);
    // }
}
