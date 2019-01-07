#[macro_use]
extern crate serde_derive;

extern crate serde_yaml;
use std::str::FromStr;
use std::fmt;
use std::collections::HashMap;
use serde::ser::{Serialize, Serializer};
use serde::de::{self, Deserialize, Deserializer, Visitor};

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
        let data = CountOfRule { count: CountOfEnum::Any, of: vec![] };
        let expected_str = "---\ncount: any\nof: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);

        let deserialized: CountOfRule = serde_yaml::from_str(&actual).unwrap();
        assert_eq!(deserialized, data);
    }

    #[test]
    fn count_of_parse_all() {
        let data = CountOfRule { count: CountOfEnum::All, of: vec![] };
        let expected_str = "---\ncount: all\nof: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);

        let deserialized: CountOfRule = serde_yaml::from_str(&actual).unwrap();
        assert_eq!(deserialized, data);
    }

    #[test]
    fn count_of_parse_number() {
        let data = CountOfRule { count: CountOfEnum::Number(6), of: vec![] };
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
                    Rule::Requirement(RequirementRule {requirement: "Core".to_owned(), optional: false}),
                    Rule::Requirement(RequirementRule {requirement: "Electives".to_owned(), optional: false}),
                ],
            }),
            requirements: [
                ("Core".to_owned(), Section::Requirement(Requirement {
                    name: "Core".to_owned(),
                    message: None,
                    department_audited: false,
                    contract: false,
                    save: vec![],
                    result: Rule::CountOf(CountOfRule {
                        count: CountOfEnum::All,
                        of: vec![
                            Rule::Course(CourseRule {department: "BIO".to_owned(), number: 123, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "BIO".to_owned(), number: 243, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "ESTH".to_owned(), number: 110, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "ESTH".to_owned(), number: 255, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "ESTH".to_owned(), number: 374, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "ESTH".to_owned(), number: 375, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "ESTH".to_owned(), number: 390, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "PSYCH".to_owned(), number: 125, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                        ],
                    }),
                })),
                ("Electives".to_owned(), Section::Requirement(Requirement {
                    name: "Electives".to_owned(),
                    message: None,
                    department_audited: false,
                    contract: false,
                    save: vec![],
                    result: Rule::CountOf(CountOfRule {
                        count: CountOfEnum::Number(2),
                        of: vec![
                            Rule::Course(CourseRule {department: "ESTH".to_owned(), number: 290, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "ESTH".to_owned(), number: 376, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "PSYCH".to_owned(), number: 230, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "NEURO".to_owned(), number: 239, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "PSYCH".to_owned(), number: 241, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::Course(CourseRule {department: "PSYCH".to_owned(), number: 247, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                            Rule::CountOf(CountOfRule {
                                count: CountOfEnum::Number(1),
                                of: vec![
                                    Rule::Course(CourseRule {department: "STAT".to_owned(), number: 110, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                                    Rule::Course(CourseRule {department: "STAT".to_owned(), number: 212, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                                    Rule::Course(CourseRule {department: "STAT".to_owned(), number: 214, term: None, section: None, year: None, semester: None, lab: None, international: None}),
                                ],
                            })
                        ],
                    }),
                })),
            ].iter().cloned().collect(),
        };

        println!("{:?}", ds);

        let s = serde_yaml::to_string(&ds).unwrap();
        println!("{}", s);
    }
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
    Course(CourseRule),
    Requirement(RequirementRule),
    CountOf(CountOfRule),
    Both(BothRule),
    Either(EitherRule),
    Given(GivenRule),
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
struct CourseRule {
    department: String,
    number: u16,
    term: Option<String>,
    section: Option<String>,
    year: Option<u16>,
    semester: Option<String>,
    lab: Option<bool>,
    international: Option<bool>,
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
        where D: Deserializer<'de>
    {
        struct CountVisitor;

        impl<'de> Visitor<'de> for CountVisitor {
            type Value = CountOfEnum;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("`count` as a number, any, or all")
            }

            fn visit_i64<E>(self, num: i64) -> Result<Self::Value, E>
                where E: de::Error
            {
                Err(E::custom(format!("negative numbers are not allowed; was `{}`", num)))
            }

            fn visit_u64<E>(self, num: u64) -> Result<Self::Value, E>
                where E: de::Error
            {
                Ok(CountOfEnum::Number(num))
            }

            fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
                where E: de::Error
            {
                match value {
                    "all" => Ok(CountOfEnum::All),
                    "any" => Ok(CountOfEnum::Any),
                    _ => Err(E::custom(format!("string must be `any` or `all`; was `{}`", value))),
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
struct SaveBlock {
}

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
