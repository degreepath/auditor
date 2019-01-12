use serde::ser::{Serialize, SerializeStruct, Serializer};
use std::str::FromStr;
use void::Void;

#[derive(Default, Debug, PartialEq, Clone, Deserialize)]
pub struct Rule {
    pub course: String,
    pub term: Option<String>,
    pub section: Option<String>,
    pub year: Option<u64>,
    pub semester: Option<String>,
    pub lab: Option<bool>,
    pub international: Option<bool>,
}

impl FromStr for Rule {
    // This implementation of `from_str` can never fail, so use the impossible
    // `Void` type as the error type.
    type Err = Void;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(Rule {
            course: String::from(s),
            ..Default::default()
        })
    }
}

impl Serialize for Rule {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match &self {
            Rule {
                term: None,
                section: None,
                year: None,
                semester: None,
                lab: None,
                international: None,
                course,
            } => {
                let mut state = serializer.serialize_struct("Rule", 1)?;
                state.serialize_field("course", course)?;
                state.end()
            }
            _ => {
                let mut state = serializer.serialize_struct("Rule", 7)?;
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn serialize() {
        let data = Rule {
            course: "STAT 214".to_string(),
            ..Default::default()
        };

        let expected_str = "---
course: STAT 214";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);
    }

    #[test]
    fn serialize_expanded() {
        let data = Rule {
            course: "STAT 214".to_string(),
            term: Some("2014-4".to_string()),
            ..Default::default()
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

        let deserialized: Rule = serde_yaml::from_str(&actual).unwrap();
        assert_eq!(deserialized, data);
    }

    #[test]
    fn deserialize_labelled() {
        let data = "---
course: STAT 214";

        let expected_struct = Rule {
            course: "STAT 214".to_string(),
            ..Default::default()
        };

        let deserialized: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }

    #[test]
    fn deserialize_expanded() {
        let data = "---
course: STAT 214
term: 2014-4
section: ~
year: ~
semester: ~
lab: ~
international: ~";

        let expected_struct = Rule {
            course: "STAT 214".to_string(),
            term: Some("2014-4".to_string()),
            ..Default::default()
        };

        let deserialized: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(deserialized, expected_struct);
    }
}
