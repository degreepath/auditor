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

mod test {
    extern crate serde_yaml;

    use crate::rules::count_of::{CountOfRule, CountOfEnum};
    use crate::rules::course::CourseRule;
    use crate::rules::requirement::RequirementRule;

    use super::*;
    use crate::rules::*;

    #[test]
    fn esth_deserialize() {
        let _area = r#"
            name: Exercise Science
            type: major
            catalog: 2014-15

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
    }

    #[test]
    fn esth_serialize() {
        let ds = AreaOfStudy {
            area_name: "Exercise Science".to_owned(),
            area_type: "major".to_owned(),
            catalog: "2015-16".to_owned(),
            result: Rule::CountOf(CountOfRule {
                count: CountOfEnum::All,
                of: vec![
                    Rule::Requirement(RequirementRule {
                        requirement: "Core".to_owned(),
                        optional: false,
                    }),
                    Rule::Requirement(RequirementRule {
                        requirement: "Electives".to_owned(),
                        optional: false,
                    }),
                ],
            }),
            requirements: [
                (
                    "Core".to_owned(),
                    Requirement {
                        name: "Core".to_owned(),
                        message: None,
                        department_audited: false,
                        contract: false,
                        save: vec![],
                        requirements: vec![],
                        result: Rule::CountOf(CountOfRule {
                            count: CountOfEnum::All,
                            of: vec![
                                Rule::Course(CourseRule {
                                    course: "BIO 123".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "BIO 243".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 110".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 255".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 374".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 375".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 390".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "PSYCH 125".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                            ],
                        }),
                    },
                ),
                (
                    "Electives".to_owned(),
                    Requirement {
                        name: "Electives".to_owned(),
                        message: None,
                        department_audited: false,
                        contract: false,
                        save: vec![],
                        requirements: vec![],
                        result: Rule::CountOf(CountOfRule {
                            count: CountOfEnum::Number(2),
                            of: vec![
                                Rule::Course(CourseRule {
                                    course: "ESTH 290".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "ESTH 376".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "PSYCH 230".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "NEURO 239".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "PSYCH 241".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::Course(CourseRule {
                                    course: "PSYCH 247".to_owned(),
                                    term: None,
                                    section: None,
                                    year: None,
                                    semester: None,
                                    lab: None,
                                    international: None,
                                }),
                                Rule::CountOf(CountOfRule {
                                    count: CountOfEnum::Number(1),
                                    of: vec![
                                        Rule::Course(CourseRule {
                                            course: "STAT 110".to_owned(),
                                            term: None,
                                            section: None,
                                            year: None,
                                            semester: None,
                                            lab: None,
                                            international: None,
                                        }),
                                        Rule::Course(CourseRule {
                                            course: "STAT 212".to_owned(),
                                            term: None,
                                            section: None,
                                            year: None,
                                            semester: None,
                                            lab: None,
                                            international: None,
                                        }),
                                        Rule::Course(CourseRule {
                                            course: "STAT 214".to_owned(),
                                            term: None,
                                            section: None,
                                            year: None,
                                            semester: None,
                                            lab: None,
                                            international: None,
                                        }),
                                    ],
                                }),
                            ],
                        }),
                    },
                ),
            ]
            .iter()
            .cloned()
            .collect(),
        };

        // println!("{:?}", ds);

        let s = serde_yaml::to_string(&ds).unwrap();
        // println!("{}", s);
    }
}
