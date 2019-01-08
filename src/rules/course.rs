use serde::de::{self, Deserialize, Deserializer, MapAccess, Visitor};
use serde::ser::{Serialize, SerializeStruct, Serializer};
use std::str::FromStr;

#[derive(Debug, PartialEq, Clone, Deserialize)]
pub struct CourseRule {
    pub course: String,
    pub term: Option<String>,
    pub section: Option<String>,
    pub year: Option<u16>,
    pub semester: Option<String>,
    pub lab: Option<bool>,
    pub international: Option<bool>,
}

/*
impl<'de> Deserialize<'de> for CourseRule {
    fn deserialize<D>(deserializer: D) -> Result<CourseRule, D::Error>
    where
        D: Deserializer<'de>,
    {
        #[derive(Deserialize)]
        #[serde(field_identifier, rename_all = "lowercase")]
        enum Field {
            Course,
            Term,
            Section,
            Year,
            Semester,
            Lab,
            International,
        }

        struct StructVisitor;

        impl<'de> Visitor<'de> for StructVisitor {
            type Value = CourseRule;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("a string `DEPT NUM` or a struct {course: DEPT NUM}")
            }

            // fn visit_str<E>(self, value: &str) -> Result<D, E>
            // where
            //     E: de::Error,
            // {
            //     Ok(FromStr::from_str(value).unwrap())
            // }

            fn visit_map<V>(self, mut map: V) -> Result<CourseRule, V::Error>
            where
                V: MapAccess<'de>,
            {
                let mut course = None;
                let mut term = None;
                let mut section = None;
                let mut year = None;
                let mut semester = None;
                let mut lab = None;
                let mut international = None;

                while let Some(key) = map.next_key()? {
                    match key {
                        Field::Course => {
                            if course.is_some() {
                                return Err(de::Error::duplicate_field("course"));
                            }
                            course = Some(map.next_value()?);
                        }
                        Field::Term => {
                            if term.is_some() {
                                return Err(de::Error::duplicate_field("term"));
                            }
                            term = Some(map.next_value()?);
                        }
                        Field::Year => {
                            if year.is_some() {
                                return Err(de::Error::duplicate_field("year"));
                            }
                            year = Some(map.next_value()?);
                        }
                        Field::Semester => {
                            if semester.is_some() {
                                return Err(de::Error::duplicate_field("semester"));
                            }
                            semester = Some(map.next_value()?);
                        }
                        Field::Section => {
                            if section.is_some() {
                                return Err(de::Error::duplicate_field("section"));
                            }
                            section = Some(map.next_value()?);
                        }
                        Field::Lab => {
                            if lab.is_some() {
                                return Err(de::Error::duplicate_field("lab"));
                            }
                            lab = Some(map.next_value()?);
                        }
                        Field::International => {
                            if international.is_some() {
                                return Err(de::Error::duplicate_field("international"));
                            }
                            international = Some(map.next_value()?);
                        }
                    }
                }

                let course = course.ok_or_else(|| de::Error::missing_field("course"))?;
                let term = term.ok_or_else(|| de::Error::missing_field("term"))?;
                let section = section.ok_or_else(|| de::Error::missing_field("section"))?;
                let year = year.ok_or_else(|| de::Error::missing_field("year"))?;
                let semester = semester.ok_or_else(|| de::Error::missing_field("semester"))?;
                let lab = lab.ok_or_else(|| de::Error::missing_field("lab"))?;
                let international =
                    international.ok_or_else(|| de::Error::missing_field("international"))?;
                Ok(CourseRule {
                    course,
                    term,
                    section,
                    year,
                    semester,
                    lab,
                    international,
                })
            }
        }

        deserializer.deserialize_any(StructVisitor)
    }
}
*/

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

mod test {
    use super::CourseRule;
    use crate::rules::Rule;

    #[test]
    fn course_rule_serialize() {
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

    #[test]
    fn course_rule_serialize_expanded() {
        let data = CourseRule {
            course: String::from("STAT 214"),
            term: Some("2014-4".to_owned()),
            section: None,
            year: None,
            semester: None,
            lab: None,
            international: None,
        };
        let expected_str = "---\ncourse: STAT 214\nterm: 2014-4\nsection: ~\nyear: ~\nsemester: ~\nlab: ~\ninternational: ~";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);

        let deserialized: CourseRule = serde_yaml::from_str(&actual).unwrap();
        assert_eq!(deserialized, data);
    }

    #[test]
    fn course_rule_deserialize_expanded() {
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

    /*
    #[test]
    fn course_rule_deserialize_expanded() {
        let data = r#"
                ---
                - course: STAT 214
                  term: 2014-4
                  section: ~
                  year: ~
                  semester: ~
                  lab: ~
                  international: ~
            "#;
        let expected_struct = vec![Rule::Course(CourseRule {
            course: "STAT 214".to_owned(),
            term: Some("2014-4".to_owned()),
            section: None,
            year: None,
            semester: None,
            lab: None,
            international: None,
        })];

        let deserialized: Vec<Rule> = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }
    */

    /*
    #[test]
    fn course_rule_deserialize_expanded_explicit() {
        let data = "---\ncourse: STAT 214\nterm: 2014-4\nsection: ~\nyear: ~\nsemester: ~\nlab: ~\ninternational: ~";
        let expected_struct = CourseRule {
            course: "STAT 214".to_owned(),
            term: Some("2014-4".to_owned()),
            section: None,
            year: None,
            semester: None,
            lab: None,
            international: None,
        };

        let deserialized: CourseRule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }
    */

    /*
    #[test]
    fn course_rule_deserialize_expanded_explicit_department_and_course_failure() {
        let data = r#"
           ---
           course: STAT 214
           term: 2014-4
           section: ~
           year: ~
           semester: ~
           lab: ~
           international: ~
       "#;
        let expected_struct = CourseRule {
            course: "STAT 214".to_owned(),
            term: Some("2014-4".to_owned()),
            section: None,
            year: None,
            semester: None,
            lab: None,
            international: None,
        };

        let deserialized: CourseRule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }
    */
}
