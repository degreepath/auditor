#[macro_use]
extern crate serde_derive;

extern crate serde_yaml;

use serde::de::{self, Deserialize, Deserializer, MapAccess, Visitor};
use serde::ser::{Serialize, SerializeStruct, Serializer};
use std::collections::HashMap;
use std::fmt;
use std::marker::PhantomData;
use std::str::FromStr;

fn serde_false() -> bool {
    false
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }

    extern crate serde_yaml;

    use crate::*;

    #[test]
    fn count_of_parse_any() {
        let data = CountOfRule {
            count: CountOfEnum::Any,
            of: vec![],
        };
        let expected_str = "---\ncount: any\nof: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);

        let deserialized: CountOfRule = serde_yaml::from_str(&actual).unwrap();
        assert_eq!(deserialized, data);
    }

    #[test]
    fn count_of_parse_all() {
        let data = CountOfRule {
            count: CountOfEnum::All,
            of: vec![],
        };
        let expected_str = "---\ncount: all\nof: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);

        let deserialized: CountOfRule = serde_yaml::from_str(&actual).unwrap();
        assert_eq!(deserialized, data);
    }

    #[test]
    fn count_of_parse_number() {
        let data = CountOfRule {
            count: CountOfEnum::Number(6),
            of: vec![],
        };
        let expected_str = "---\ncount: 6\nof: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);

        let deserialized: CountOfRule = serde_yaml::from_str(&actual).unwrap();
        assert_eq!(deserialized, data);
    }

    #[test]
    fn basic_area_parse() {
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
                    Section::Requirement(Requirement {
                        name: "Core".to_owned(),
                        message: None,
                        department_audited: false,
                        contract: false,
                        save: vec![],
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
                    }),
                ),
                (
                    "Electives".to_owned(),
                    Section::Requirement(Requirement {
                        name: "Electives".to_owned(),
                        message: None,
                        department_audited: false,
                        contract: false,
                        save: vec![],
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
                    }),
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

    #[test]
    fn course_rule_serialize_simple() {
        let data = CourseRule {
            course: "STAT 214".to_owned(),
            term: None,
            section: None,
            year: None,
            semester: None,
            lab: None,
            international: None,
        };
        let expected_str = "---\nSTAT 214";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);
    }

    // #[test]
    // fn course_rule_serialize_expanded() {
    //     let data = CourseRule { course: String::from("STAT 214"), term: Some("2014-4".to_owned()), section: None, year: None, semester: None, lab: None, international: None };
    //     let expected_str = "---\ncourse: STAT 214\nterm: 2014-4\nsection: ~\nyear: ~\nsemester: ~\nlab: ~\ninternational: ~";

    //     let actual = serde_yaml::to_string(&data).unwrap();
    //     assert_eq!(actual, expected_str);

    //     let deserialized: CourseRule = serde_yaml::from_str(&actual).unwrap();
    //     println!("{:?}", deserialized);
    //     assert_eq!(deserialized, data);
    // }

    #[test]
    fn course_rule_deserialize_simple_ish() {
        let data = "---\ncourse: STAT 214";
        let expected_struct = CourseRule {
            course: "STAT 214".to_owned(),
            term: None,
            section: None,
            year: None,
            semester: None,
            lab: None,
            international: None,
        };

        let deserialized: CourseRule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }

    #[test]
    fn course_rule_deserialize_simple() {
        let data = "---\n- STAT 214";
        let expected_struct = vec![Rule::Course(CourseRule {
            course: "STAT 214".to_owned(),
            term: None,
            section: None,
            year: None,
            semester: None,
            lab: None,
            international: None,
        })];

        let deserialized: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }

    // #[test]
    // fn course_rule_deserialize_expanded() {
    //     let data = r#"
    //             ---
    //             - course: STAT 214
    //               term: 2014-4
    //               section: ~
    //               year: ~
    //               semester: ~
    //               lab: ~
    //               international: ~
    //         "#;
    //     let expected_struct = vec![Rule::Course(CourseRule {
    //         course: "STAT 214".to_owned(),
    //         term: Some("2014-4".to_owned()),
    //         section: None,
    //         year: None,
    //         semester: None,
    //         lab: None,
    //         international: None,
    //     })];

    //     let deserialized: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
    //     assert_eq!(deserialized, expected_struct);
    // }

    //    #[test]
    //    fn course_rule_deserialize_expanded_explicit() {
    //        let data = "---\ncourse: STAT 214\nterm: 2014-4\nsection: ~\nyear: ~\nsemester: ~\nlab: ~\ninternational: ~";
    //        let expected_struct = CourseRule { course: "STAT 214".to_owned(), term: Some("2014-4".to_owned()), section: None, year: None, semester: None, lab: None, international: None };
    //
    //        let deserialized: CourseRule = serde_yaml::from_str(&data).unwrap();
    //        assert_eq!(deserialized, expected_struct);
    //    }

    //    #[test]
    //    fn course_rule_deserialize_expanded_explicit_department_and_course_failure() {
    //        let data = r#"
    //            ---
    //            course: STAT 214
    //            term: 2014-4
    //            section: ~
    //            year: ~
    //            semester: ~
    //            lab: ~
    //            international: ~
    //        "#;
    //        let expected_struct = CourseRule { course: "STAT 214".to_owned(), term: Some("2014-4".to_owned()), section: None, year: None, semester: None, lab: None, international: None };
    //
    //        let deserialized: CourseRule = serde_yaml::from_str(&data).unwrap();
    //        assert_eq!(deserialized, expected_struct);
    //    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct AreaOfStudy {
    #[serde(rename = "name")]
    area_name: String,
    #[serde(rename = "type")]
    area_type: String,
    catalog: String,

    result: Rule,
    requirements: HashMap<String, Section>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
enum Rule {
    Course(#[serde(deserialize_with = "string_or_struct")] CourseRule),
    Requirement(RequirementRule),
    CountOf(CountOfRule),
    Both(BothRule),
    Either(EitherRule),
    Given(GivenRule),
}

#[derive(Debug, PartialEq, Clone, Deserialize)]
struct CourseRule {
    course: String,
    term: Option<String>,
    section: Option<String>,
    year: Option<u16>,
    semester: Option<String>,
    lab: Option<bool>,
    international: Option<bool>,
}

// impl<'de> Deserialize<'de> for CourseRule {
//     fn deserialize<D>(deserializer: D) -> Result<CourseRule, D::Error>
//     where
//         D: Deserializer<'de>,
//     {
//         #[derive(Deserialize)]
//         #[serde(field_identifier, rename_all = "lowercase")]
//         enum Field {
//             Course,
//             Term,
//             Section,
//             Year,
//             Semester,
//             Lab,
//             International,
//         }

//         struct StructVisitor;

//         impl<'de> Visitor<'de> for StructVisitor {
//             type Value = CourseRule;

//             fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
//                 formatter.write_str("a string `DEPT NUM` or a struct {course: DEPT NUM}")
//             }

//             // fn visit_str<E>(self, value: &str) -> Result<D, E>
//             // where
//             //     E: de::Error,
//             // {
//             //     Ok(FromStr::from_str(value).unwrap())
//             // }

//             fn visit_map<V>(self, mut map: V) -> Result<CourseRule, V::Error>
//             where
//                 V: MapAccess<'de>,
//             {
//                 let mut course = None;
//                 let mut term = None;
//                 let mut section = None;
//                 let mut year = None;
//                 let mut semester = None;
//                 let mut lab = None;
//                 let mut international = None;

//                 while let Some(key) = map.next_key()? {
//                     match key {
//                         Field::Course => {
//                             if course.is_some() {
//                                 return Err(de::Error::duplicate_field("course"));
//                             }
//                             course = Some(map.next_value()?);
//                         }
//                         Field::Term => {
//                             if term.is_some() {
//                                 return Err(de::Error::duplicate_field("term"));
//                             }
//                             term = Some(map.next_value()?);
//                         }
//                         Field::Year => {
//                             if year.is_some() {
//                                 return Err(de::Error::duplicate_field("year"));
//                             }
//                             year = Some(map.next_value()?);
//                         }
//                         Field::Semester => {
//                             if semester.is_some() {
//                                 return Err(de::Error::duplicate_field("semester"));
//                             }
//                             semester = Some(map.next_value()?);
//                         }
//                         Field::Section => {
//                             if section.is_some() {
//                                 return Err(de::Error::duplicate_field("section"));
//                             }
//                             section = Some(map.next_value()?);
//                         }
//                         Field::Lab => {
//                             if lab.is_some() {
//                                 return Err(de::Error::duplicate_field("lab"));
//                             }
//                             lab = Some(map.next_value()?);
//                         }
//                         Field::International => {
//                             if international.is_some() {
//                                 return Err(de::Error::duplicate_field("international"));
//                             }
//                             international = Some(map.next_value()?);
//                         }
//                     }
//                 }

//                 let course = course.ok_or_else(|| de::Error::missing_field("course"))?;
//                 let term = term.ok_or_else(|| de::Error::missing_field("term"))?;
//                 let section = section.ok_or_else(|| de::Error::missing_field("section"))?;
//                 let year = year.ok_or_else(|| de::Error::missing_field("year"))?;
//                 let semester = semester.ok_or_else(|| de::Error::missing_field("semester"))?;
//                 let lab = lab.ok_or_else(|| de::Error::missing_field("lab"))?;
//                 let international =
//                     international.ok_or_else(|| de::Error::missing_field("international"))?;
//                 Ok(CourseRule {
//                     course,
//                     term,
//                     section,
//                     year,
//                     semester,
//                     lab,
//                     international,
//                 })
//             }
//         }

//         deserializer.deserialize_any(StructVisitor)
//     }
// }

use void::Void;
impl FromStr for CourseRule {
    // This implementation of `from_str` can never fail, so use the impossible
    // `Void` type as the error type.
    type Err = Void;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        println!("called fromstr for courserule");
        Ok(CourseRule {
            course: String::from(s),
            term: None,
            section: None,
            year: None,
            semester: None,
            lab: None,
            international: None,
        })
    }
}

impl Serialize for CourseRule {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match &self {
            CourseRule {
                term: None,
                section: None,
                year: None,
                semester: None,
                lab: None,
                international: None,
                course,
            } => serializer.serialize_str(format!("{}", course).as_str()),
            _ => {
                let mut state = serializer.serialize_struct("CourseRule", 7)?;
                state.serialize_field("course", &format!("{}", &self.course))?;
                state.serialize_field("term", &self.term)?;
                state.serialize_field("section", &self.section)?;
                state.serialize_field("year", &self.year)?;
                state.serialize_field("semester", &self.semester)?;
                state.serialize_field("lab", &self.lab)?;
                state.serialize_field("international", &self.international)?;
                state.end()
            }
        }
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct RequirementRule {
    requirement: String,
    #[serde(default = "serde_false")]
    optional: bool,
}

#[derive(Debug, PartialEq, Clone)]
enum CountOfEnum {
    All,
    Any,
    Number(u64),
}

impl Serialize for CountOfEnum {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match &self {
            CountOfEnum::All => serializer.serialize_str("all"),
            CountOfEnum::Any => serializer.serialize_str("any"),
            CountOfEnum::Number(n) => serializer.serialize_u64(*n),
        }
    }
}

impl<'de> Deserialize<'de> for CountOfEnum {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct CountVisitor;

        impl<'de> Visitor<'de> for CountVisitor {
            type Value = CountOfEnum;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("`count` as a number, any, or all")
            }

            fn visit_i64<E>(self, num: i64) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                Err(E::custom(format!(
                    "negative numbers are not allowed; was `{}`",
                    num
                )))
            }

            fn visit_u64<E>(self, num: u64) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                Ok(CountOfEnum::Number(num))
            }

            fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                match value {
                    "all" => Ok(CountOfEnum::All),
                    "any" => Ok(CountOfEnum::Any),
                    _ => Err(E::custom(format!(
                        "string must be `any` or `all`; was `{}`",
                        value
                    ))),
                }
            }
        }

        deserializer.deserialize_any(CountVisitor)
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct CountOfRule {
    count: CountOfEnum,
    of: Vec<Rule>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct BothRule {
    both: (Box<Rule>, Box<Rule>),
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct EitherRule {
    either: (Box<Rule>, Box<Rule>),
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
enum GivenRule {
    AllCourses(GivenAllCoursesRule),
    TheseCourses(GivenTheseCoursesRule),
    TheseRequirements(GivenTheseRequirementsRule),
    AreasOfStudy(GivenAreasOfStudyRule),
    NamedVariable(GivenNamedVariableRule),
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct GivenAllCoursesRule {
    given: String,
    what: GivenWhatToGiveEnum,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct DoAction {
    command: RuleAction,
    lhs: String,
    operator: RuleOperator,
    rhs: String,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct GivenTheseCoursesRule {
    given: String,
    courses: Vec<CourseRule>,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct GivenTheseRequirementsRule {
    given: String,
    requirements: Vec<RequirementRule>,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct GivenNamedVariableRule {
    given: String,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    what: GivenWhatToGiveEnum,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct GivenWhereClause {
    key: String,
    value: String,
    operation: GivenWhereOp,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
enum GivenWhereOp {
    Eq,
    NotEq,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct GivenLimiter {}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct GivenAreasOfStudyRule {
    given: String,
    #[serde(rename = "where")]
    filter: Vec<GivenWhereClause>,
    limit: Vec<GivenLimiter>,
    what: GivenWhatToGiveAreasEnum,
    #[serde(rename = "do")]
    action: DoAction,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
enum GivenWhatToGiveEnum {
    Courses,
    DistinctCourses,
    Credits,
    Terms,
    Grades,
}

impl FromStr for GivenWhatToGiveEnum {
    type Err = ();

    fn from_str(s: &str) -> Result<GivenWhatToGiveEnum, ()> {
        match s {
            "courses" => Ok(GivenWhatToGiveEnum::Courses),
            "distinct courses" => Ok(GivenWhatToGiveEnum::DistinctCourses),
            "credits" => Ok(GivenWhatToGiveEnum::Credits),
            "terms" => Ok(GivenWhatToGiveEnum::Terms),
            "Grades" => Ok(GivenWhatToGiveEnum::Grades),
            _ => Err(()),
        }
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
enum GivenWhatToGiveAreasEnum {
    #[serde(rename = "areas of study")]
    AreasOfStudy,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
enum RuleOperator {
    #[serde(rename = "<")]
    LessThan,
    #[serde(rename = "<=")]
    LessThanOrEqualTo,
    #[serde(rename = "=")]
    EqualTo,
    #[serde(rename = ">")]
    GreaterThan,
    #[serde(rename = ">=")]
    GreaterThanOrEqualTo,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
enum RuleAction {
    Count,
    Sum,
    Average,
    Minimum,
    Difference,
    NamedVariable(String),
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct Requirement {
    name: String,
    message: Option<String>,
    #[serde(default = "serde_false")]
    department_audited: bool,
    result: Rule,
    #[serde(default = "serde_false")]
    contract: bool,
    save: Vec<SaveBlock>,
}

// should be a superset of GivenRule...
#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct SaveBlock {}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
enum Section {
    Subsection(Subsection),
    Requirement(Requirement),
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct Subsection {
    message: Option<String>,
}

fn string_or_struct<'de, T, D>(deserializer: D) -> Result<T, D::Error>
where
    T: Deserialize<'de> + FromStr<Err = Void>,
    D: Deserializer<'de>,
{
    // This is a Visitor that forwards string types to T's `FromStr` impl and
    // forwards map types to T's `Deserialize` impl. The `PhantomData` is to
    // keep the compiler from complaining about T being an unused generic type
    // parameter. We need T in order to know the Value type for the Visitor
    // impl.
    struct StringOrStruct<T>(PhantomData<fn() -> T>);

    impl<'de, T> Visitor<'de> for StringOrStruct<T>
    where
        T: Deserialize<'de> + FromStr<Err = Void>,
    {
        type Value = T;

        fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
            formatter.write_str("string or map")
        }

        fn visit_str<E>(self, value: &str) -> Result<T, E>
        where
            E: de::Error,
        {
            println!("called visitstr for courserule");
            Ok(FromStr::from_str(value).unwrap())
        }

        fn visit_map<M>(self, visitor: M) -> Result<T, M::Error>
        where
            M: MapAccess<'de>,
        {
            // `MapAccessDeserializer` is a wrapper that turns a `MapAccess`
            // into a `Deserializer`, allowing it to be used as the input to T's
            // `Deserialize` implementation. T then deserializes itself using
            // the entries from the map visitor.
            Deserialize::deserialize(de::value::MapAccessDeserializer::new(visitor))
        }
    }

    deserializer.deserialize_any(StringOrStruct(PhantomData))
}
