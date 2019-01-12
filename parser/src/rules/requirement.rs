use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    pub requirement: String,
    #[serde(default = "util::serde_false")]
    pub optional: bool,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn serialize() {
        let data = Rule {
            requirement: String::from("Name"),
            optional: false,
        };
        let expected = "---
requirement: Name
optional: false";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize() {
        let data = "---
requirement: Name
optional: false";
        let expected = Rule {
            requirement: String::from("Name"),
            optional: false,
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_with_defaults() {
        let data = "---
requirement: Name";
        let expected = Rule {
            requirement: String::from("Name"),
            optional: false,
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }
}
