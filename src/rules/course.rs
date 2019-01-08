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

use void::Void;
impl FromStr for CourseRule {
    // This implementation of `from_str` can never fail, so use the impossible
    // `Void` type as the error type.
    type Err = Void;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
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
            } => {
                let mut state = serializer.serialize_struct("CourseRule", 1)?;
                state.serialize_field("course", course)?;
                state.end()
            }
            _ => {
                let mut state = serializer.serialize_struct("CourseRule", 7)?;
                state.serialize_field("course", &self.course)?;
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

mod tests {
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
        let expected_str = "---
course: STAT 214";

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
        let expected_str = "---
course: STAT 214
term: 2014-4
section: ~
year: ~
semester: ~
lab: ~
international: ~";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);

        let deserialized: CourseRule = serde_yaml::from_str(&actual).unwrap();
        assert_eq!(deserialized, data);
    }

    #[test]
    fn course_rule_deserialize_labelled() {
        let data = "---
course: STAT 214";
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
        let data = "---
- STAT 214";
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

    #[test]
    fn course_rule_deserialize_expanded() {
        let data = "
---
- course: STAT 214
  term: 2014-4
  section: ~
  year: ~
  semester: ~
  lab: ~
  international: ~
";
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

    #[test]
    fn course_rule_deserialize_expanded_explicit() {
        let data = "---
course: STAT 214
term: 2014-4
section: ~
year: ~
semester: ~
lab: ~
international: ~";
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
}
