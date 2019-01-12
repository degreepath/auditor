use crate::rules::Rule as AnyRule;
use serde::de::{self, Deserialize, Deserializer, Visitor};
use serde::ser::{Serialize, Serializer};
use std::fmt;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    pub count: Counter,
    pub of: Vec<AnyRule>,
}

#[derive(Debug, PartialEq, Clone)]
pub enum Counter {
    All,
    Any,
    Number(u64),
}

impl fmt::Display for Counter {
    fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
        let what: String = match &self {
            Counter::All => "all".to_string(),
            Counter::Any => "any".to_string(),
            Counter::Number(n) => format!("{}", n),
        };
        fmt.write_str(&what)
    }
}

impl Serialize for Counter {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match &self {
            Counter::All => serializer.serialize_str("all"),
            Counter::Any => serializer.serialize_str("any"),
            Counter::Number(n) => serializer.serialize_u64(*n),
        }
    }
}

impl<'de> Deserialize<'de> for Counter {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct CountVisitor;

        impl<'de> Visitor<'de> for CountVisitor {
            type Value = Counter;

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
                Ok(Counter::Number(num))
            }

            fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                match value {
                    "all" => Ok(Counter::All),
                    "any" => Ok(Counter::Any),
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn serialize_count_of_any() {
        let data = Rule {
            count: Counter::Any,
            of: vec![],
        };

        let expected_str = "---
count: any
of: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);
    }

    #[test]
    fn deserialize_count_of_any() {
        let data = "---
count: any
of: []";

        let expected_struct = Rule {
            count: Counter::Any,
            of: vec![],
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn serialize_count_of_all() {
        let data = Rule {
            count: Counter::All,
            of: vec![],
        };

        let expected_str = "---
count: all
of: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);
    }

    #[test]
    fn deserialize_count_of_all() {
        let data = "---
count: all
of: []";

        let expected_struct = Rule {
            count: Counter::All,
            of: vec![],
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn serialize_count_of_number() {
        let data = Rule {
            count: Counter::Number(6),
            of: vec![],
        };

        let expected_str = "---
count: 6
of: []";

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected_str);
    }

    #[test]
    fn deserialize_count_of_number() {
        let data = "---
count: 6
of: []";

        let expected_struct = Rule {
            count: Counter::Number(6),
            of: vec![],
        };

        let actual: Rule = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected_struct);
    }
}
