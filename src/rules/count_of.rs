use crate::rules::Rule;
use serde::de::{self, Deserialize, Deserializer, Visitor};
use serde::ser::{Serialize, Serializer};
use std::fmt;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct CountOfRule {
    pub count: CountOfEnum,
    pub of: Vec<Rule>,
}

#[derive(Debug, PartialEq, Clone)]
pub enum CountOfEnum {
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

mod test {
    use super::*;

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
}
