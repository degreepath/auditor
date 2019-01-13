use serde::ser::{Serializer, Serialize};
use serde::de::{Deserializer, Deserialize};
use crate::util;

use super::action;
use crate::rules::given::action::ParseError;

use std::collections::HashMap;
use std::fmt;
use std::str::FromStr;

pub type Clause = HashMap<String, WrappedValue>;

pub fn deserialize_with<'de, D>(deserializer: D) -> Result<Option<Clause>, D::Error>
where
    D: Deserializer<'de>,
{
    #[derive(Deserialize)]
    struct Wrapper(#[serde(deserialize_with = "util::string_or_struct_parseerror")] WrappedValue);

    let v = HashMap::deserialize(deserializer)?;
    Ok(Some(v))
}

#[derive(Debug, PartialEq, Deserialize, Clone)]
pub enum WrappedValue {
    Single(TaggedValue),
    Or([TaggedValue; 2]),
    And([TaggedValue; 2]),
}

impl WrappedValue {
    pub fn is_true(&self) -> bool {
        match &self {
            WrappedValue::Single(val) => val.is_true(),
            _ => false,
        }
    }
}

impl FromStr for WrappedValue {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let or_bits: Vec<_> = s.split(" | ").collect();
        match or_bits.as_slice() {
            [a, b] => return Ok(WrappedValue::Or([
                a.parse::<TaggedValue>()?,
                b.parse::<TaggedValue>()?,
            ])),
            _ => (),
        };

        let and_bits: Vec<_> = s.split(" & ").collect();
        match and_bits.as_slice() {
            [a, b] => return Ok(WrappedValue::And([
                a.parse::<TaggedValue>()?,
                b.parse::<TaggedValue>()?,
            ])),
            _ => (),
        };

        Ok(WrappedValue::Single(s.parse::<TaggedValue>()?))
    }
}

impl fmt::Display for WrappedValue {
    fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
        let desc = match &self {
            WrappedValue::And([a, b]) => format!("{} & {}", a, b),
            WrappedValue::Or([a, b]) => format!("{} | {}", a, b),
            WrappedValue::Single(val) => format!("{}", val),
        };
        fmt.write_str(&desc)
    }
}

impl Serialize for WrappedValue {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&format!("{}", &self))
    }
}

#[derive(Debug, PartialEq, Deserialize, Clone)]
pub struct TaggedValue {
    pub op: action::Operator,
    pub value: Value,
}

impl TaggedValue {
    pub fn is_true(&self) -> bool {
        match &self.op {
            action::Operator::EqualTo => self.value == true,
            _ => false,
        }
    }
}

impl FromStr for TaggedValue {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let splitted: Vec<_> = s.split_whitespace().collect();

        match splitted.as_slice() {
            [value] => {
                let value = value.parse::<Value>()?;

                Ok(TaggedValue {
                    op: action::Operator::EqualTo,
                    value,
                })
            }
            [op, value] => {
                let op = op.parse::<action::Operator>()?;
                let value = value.parse::<Value>()?;

                Ok(TaggedValue {
                    op, value
                })
            }
            _ => Err(ParseError::InvalidAction),
        }
    }
}

impl fmt::Display for TaggedValue {
    fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
        let desc = format!("{} {}", self.op, self.value);
        fmt.write_str(&desc)
    }
}

impl Serialize for TaggedValue {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&format!("{}", &self))
    }
}

#[derive(Debug, PartialEq, Deserialize, Clone)]
pub enum Constant {
    #[serde(rename = "graduation-year")]
    GraduationYear,
}

impl fmt::Display for Constant {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match &self {
            Constant::GraduationYear => write!(f, "graduation-year"),
        }
    }
}

impl FromStr for Constant {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();

        match s {
            "graduation-year" => Ok(Constant::GraduationYear),
            _ => Err(ParseError::UnknownCommand),
        }
    }
}

impl Serialize for Constant {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&format!("{}", &self))
    }
}

#[derive(Debug, PartialEq, Deserialize, Clone)]
pub enum Value {
    Constant(Constant),
    Bool(bool),
    Integer(u64),
    Float(f64),
    String(String),
}

impl From<String> for Value {
    fn from(s: String) -> Value {
        Value::String(s)
    }
}

impl From<&str> for Value {
    fn from(s: &str) -> Value {
        Value::String(s.to_string())
    }
}

impl From<u64> for Value {
    fn from(i: u64) -> Value {
        Value::Integer(i)
    }
}

impl From<bool> for Value {
    fn from(b: bool) -> Value {
        Value::Bool(b)
    }
}

impl FromStr for Value {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if let Ok(constant) = s.parse::<Constant>() {
            return Ok(Value::Constant(constant));
        }

        if let Ok(num) = s.parse::<u64>() {
            return Ok(Value::Integer(num));
        }

        if let Ok(num) = s.parse::<f64>() {
            return Ok(Value::Float(num));
        }

        if let Ok(b) = s.parse::<bool>() {
            return Ok(Value::Bool(b));
        }

        Ok(Value::String(s.to_string()))
    }
}

impl PartialEq<bool> for Value {
    fn eq(&self, rhs: &bool) -> bool {
        match &self {
            Value::Bool(b) => b == rhs,
            _ => false,
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
        let desc = match &self {
            Value::String(s) => format!("{}", s),
            Value::Integer(n) => format!("{}", n),
            Value::Float(n) => format!("{:.2}", n),
            Value::Bool(b) => format!("{}", b),
            Value::Constant(s) => format!("{}", s),
        };
        fmt.write_str(&desc)
    }
}

impl Serialize for Value {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&format!("{}", &self))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::action::Operator;

    #[test]
    fn serialize_simple() {
        let data: Clause = hashmap! {
            "level".into() => "100".parse::<WrappedValue>().unwrap(),
        };

        let expected = r#"---
level: "= 100""#;

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn serialize_or() {
        let data: Clause = hashmap! {
            "level".into() => "100 | 200".parse::<WrappedValue>().unwrap(),
        };

        let expected = r#"---
level: "= 100 | = 200""#;

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);

        let data: Clause = hashmap! {
            "level".into() =>  "< 100 | 200".parse::<WrappedValue>().unwrap(),
        };

        let expected = r#"---
level: "< 100 | = 200""#;

        let actual = serde_yaml::to_string(&data).unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_simple() {
        let data = r#"gereqs: 'FYW'"#;

        let expected: Clause = hashmap! {
            "gereqs".into() => WrappedValue::Single(TaggedValue {op: Operator::EqualTo, value: Value::String("FYW".into())}),
        };

        let actual: Clause = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);

        let data = r#"gereqs: 'MCD | MCG'"#;

        let expected: Clause = hashmap! {
            "gereqs".into() => WrappedValue::Or([
                TaggedValue {op: Operator::EqualTo, value: Value::String("MCD".into())},
                TaggedValue {op: Operator::EqualTo, value: Value::String("MCG".into())},
            ])
        };

        let actual: Clause = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);

        let data = r#"level: '>= 200'"#;

        let expected: Clause = hashmap! {
            "level".into() => WrappedValue::Single(TaggedValue {op: Operator::GreaterThanEqualTo, value: Value::Integer(200)}),
        };

        let actual: Clause = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);

        let data = r#"graded: 'true'"#;

        let expected: Clause = hashmap! {
            "level".into() => WrappedValue::Single(TaggedValue {op: Operator::EqualTo, value: Value::Bool(true)}),
        };

        let actual: Clause = serde_yaml::from_str(&data).unwrap();
        assert_eq!(actual, expected);
    }
}

/*

> where: { gereqs: 'FYW' }
< where: { gereqs: { op: Equal, value: { String: 'FYW' } } }

---

> where: { gereqs: 'MCD | MCG' }
< where: { gereqs: { op: ~, value: { Or: [{ op: Equal, value: { String: 'MCD' } }, { op: Equal, value: { String: 'MCG' } }] } } }

---

> where: { level: '>= 200' }
< where: { level: { op: GreaterThanOrEqual, value: { Integer: 200 } } }

---

> where: { graded: true }
< where: { level: { op: Equal, value: { Bool: true } } }

*/
