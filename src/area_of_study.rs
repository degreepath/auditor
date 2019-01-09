use crate::requirement::Requirement;
use crate::rules::Rule;
use std::collections::HashMap;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct AreaOfStudy {
    #[serde(rename = "name")]
    pub area_name: String,
    #[serde(rename = "type")]
    pub area_type: String,
    pub catalog: String,
    pub result: Rule,
    pub requirements: HashMap<String, Requirement>,
}

#[cfg(test)]
mod tests {
    use crate::rules::count_of::{CountOfEnum, CountOfRule};
    use crate::rules::course::CourseRule;
    use crate::rules::requirement::RequirementRule;
    use crate::rules::Rule;

    use super::*;

    #[test]
    fn deserialize() {
        let data = r#"
            name: Exercise Science
            type: major
            catalog: 2015-16

            result:
              count: all
              of:
                - requirement: Core
                - requirement: Electives

            requirements:
              Core:
                result:
                  count: all
                  of:
                    - BIO 143
                    - BIO 243
                    - ESTH 110
                    - ESTH 255
                    - ESTH 374
                    - ESTH 375
                    - ESTH 390
                    - PSYCH 125

              Electives:
                result:
                  count: 2
                  of:
                    - ESTH 290
                    - ESTH 376
                    - PSYCH 230
                    - NEURO 239
                    - PSYCH 241
                    - PSYCH 247
                    - {count: 1, of: [STAT 110, STAT 212, STAT 214]}
        "#;

        let expected_struct = AreaOfStudy {
            area_name: "Exercise Science".to_string(),
            area_type: "major".to_string(),
            catalog: "2015-16".to_string(),
            result: Rule::CountOf(CountOfRule {
                count: CountOfEnum::All,
                of: vec![
                    Rule::Requirement(RequirementRule {
                        requirement: "Core".to_string(),
                        optional: false,
                    }),
                    Rule::Requirement(RequirementRule {
                        requirement: "Electives".to_string(),
                        optional: false,
                    }),
                ],
            }),
            requirements: [
                (
                    "Core".to_string(),
                    Requirement {
                        message: None,
                        department_audited: false,
                        contract: false,
                        save: vec![],
                        requirements: HashMap::new(),
                        result: Some(Rule::CountOf(CountOfRule {
                            count: CountOfEnum::All,
                            of: vec![
                                Rule::Course(CourseRule {
                                    course: "BIO 143".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "BIO 243".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 110".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 255".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 374".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 375".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 390".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "PSYCH 125".to_string(),
                                    ..Default::default()
                                }),
                            ],
                        })),
                    },
                ),
                (
                    "Electives".to_string(),
                    Requirement {
                        message: None,
                        department_audited: false,
                        contract: false,
                        save: vec![],
                        requirements: HashMap::new(),
                        result: Some(Rule::CountOf(CountOfRule {
                            count: CountOfEnum::Number(2),
                            of: vec![
                                Rule::Course(CourseRule {
                                    course: "ESTH 290".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 376".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "PSYCH 230".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "NEURO 239".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "PSYCH 241".to_string(),
                                    ..Default::default()
                                }),
                                Rule::Course(CourseRule {
                                    course: "PSYCH 247".to_string(),
                                    ..Default::default()
                                }),
                                Rule::CountOf(CountOfRule {
                                    count: CountOfEnum::Number(1),
                                    of: vec![
                                        Rule::Course(CourseRule {
                                            course: "STAT 110".to_string(),
                                            ..Default::default()
                                        }),
                                        Rule::Course(CourseRule {
                                            course: "STAT 212".to_string(),
                                            ..Default::default()
                                        }),
                                        Rule::Course(CourseRule {
                                            course: "STAT 214".to_string(),
                                            ..Default::default()
                                        }),
                                    ],
                                }),
                            ],
                        })),
                    },
                ),
            ]
            .iter()
            .cloned()
            .collect(),
        };

        let actual: AreaOfStudy = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected_struct);
    }
}
