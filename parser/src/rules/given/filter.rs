use crate::util::{self, Oxford};
use serde::de::{Deserialize, Deserializer};
use serde::ser::{Serialize, Serializer};

use super::action::Operator;

use std::collections::HashMap;
use std::fmt;
use std::str::FromStr;

pub type Clause = HashMap<String, WrappedValue>;

impl crate::rules::traits::PrettyPrint for Clause {
    fn print(&self) -> Result<String, std::fmt::Error> {
        // TODO: don't rely on fmt::Display to display the Values

        let mut clauses = vec![];

        if let Some(gereq) = self.get("gereqs") {
            match gereq {
                WrappedValue::Single(v) => {
                    clauses.push(format!("with the “{}” general education attribute", v.print()?))
                }
                WrappedValue::Or(_) | WrappedValue::And(_) => {
                    // TODO: figure out how to quote these
                    clauses.push(format!("with the {} general education attribute", gereq.print()?));
                }
            };
        }

        if let Some(semester) = self.get("semester") {
            match semester {
                WrappedValue::Single(v) => clauses.push(format!("during {} semesters", v.print()?)),
                WrappedValue::Or(_) | WrappedValue::And(_) => {
                    clauses.push(format!("during a {} semester", semester.print()?))
                }
            };
        }

        if let Some(year) = self.get("year") {
            match year {
                WrappedValue::Single(TaggedValue {
                    op: Operator::EqualTo,
                    value: Value::Integer(n),
                }) => clauses.push(format!("during the {} academic year", util::expand_year(*n, "dual"))),
                WrappedValue::Or(_) | WrappedValue::And(_) => {
                    // TODO: implement a .map() function on WrappedValue?
                    // to allow something like `year.map(util::expand_year).print()?`
                    clauses.push(format!("during the {} academic years", year.print()?));
                }
                _ => unimplemented!(),
            }
        }

        if let Some(institution) = self.get("institution") {
            match institution {
                WrappedValue::Single(v) => clauses.push(format!("at {}", v.print()?)),
                WrappedValue::Or(_) => {
                    clauses.push(format!("at either {}", institution.print()?));
                }
                WrappedValue::And(_) => unimplemented!(),
            }
        }

        if let Some(department) = self.get("department") {
            match department {
                WrappedValue::Single(TaggedValue {
                    op: Operator::EqualTo,
                    value: v,
                }) => clauses.push(format!("within the {} department", v.print()?)),
                WrappedValue::Single(TaggedValue {
                    op: Operator::NotEqualTo,
                    value: v,
                }) => clauses.push(format!("outside of the {} department", v.print()?)),
                WrappedValue::Single(TaggedValue { op: _, value: _ }) => {
                    unimplemented!("only implemented for = and !=")
                }
                WrappedValue::Or(_) => {
                    clauses.push(format!("within either of the {} departments", department.print()?));
                }
                WrappedValue::And(_) => unimplemented!(),
            }
        }

        // TODO: handle other filterable keys

        Ok(clauses.oxford("and"))
    }
}

pub fn deserialize_with<'de, D>(deserializer: D) -> Result<Option<Clause>, D::Error>
where
    D: Deserializer<'de>,
{
    #[derive(Deserialize)]
    // TODO: support integers and booleans as well as string/struct
    struct Wrapper(#[serde(deserialize_with = "util::string_or_struct_parseerror")] WrappedValue);

    // TODO: improve this to not transmute the hashmap right after creation
    let v: Result<HashMap<String, Wrapper>, D::Error> = HashMap::deserialize(deserializer);

    match v {
        Ok(v) => {
            let transmuted: Clause = v.into_iter().map(|(k, v)| (k, v.0)).collect();
            Ok(Some(transmuted))
        }
        Err(err) => Err(err),
    }
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

impl crate::rules::traits::PrettyPrint for WrappedValue {
    fn print(&self) -> Result<String, std::fmt::Error> {
        match &self {
            WrappedValue::Single(v) => Ok(format!("{}", v.print()?)),
            WrappedValue::Or([a, b]) => Ok(format!("{} or {}", a.print()?, b.print()?)),
            WrappedValue::And([a, b]) => Ok(format!("{} and {}", a.print()?, b.print()?)),
        }
    }
}

impl FromStr for WrappedValue {
    type Err = util::ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let or_bits: Vec<_> = s.split(" | ").collect();
        match or_bits.as_slice() {
            [a, b] => return Ok(WrappedValue::Or([a.parse::<TaggedValue>()?, b.parse::<TaggedValue>()?])),
            _ => (),
        };

        let and_bits: Vec<_> = s.split(" & ").collect();
        match and_bits.as_slice() {
            [a, b] => {
                return Ok(WrappedValue::And([
                    a.parse::<TaggedValue>()?,
                    b.parse::<TaggedValue>()?,
                ]))
            }
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
    pub op: Operator,
    pub value: Value,
}

impl TaggedValue {
    pub fn is_true(&self) -> bool {
        match &self.op {
            Operator::EqualTo => self.value == true,
            _ => false,
        }
    }
}

impl FromStr for TaggedValue {
    type Err = util::ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.get(0..1) {
            Some("!") | Some("<") | Some(">") | Some("=") => {
                let splitted: Vec<_> = s.split_whitespace().collect();

                match splitted.as_slice() {
                    [value] => {
                        let value = value.parse::<Value>()?;

                        Ok(TaggedValue {
                            op: Operator::EqualTo,
                            value,
                        })
                    }
                    [op, value] => {
                        let op = op.parse::<Operator>()?;
                        let value = value.parse::<Value>()?;

                        Ok(TaggedValue { op, value })
                    }
                    _ => {
                        // println!("{:?}", splitted);
                        Err(util::ParseError::InvalidAction)
                    }
                }
            }
            _ => {
                let value = s.parse::<Value>()?;

                Ok(TaggedValue {
                    op: Operator::EqualTo,
                    value,
                })
            }
        }
    }
}

impl crate::rules::traits::PrettyPrint for TaggedValue {
    fn print(&self) -> Result<String, std::fmt::Error> {
        match &self.op {
            Operator::EqualTo => Ok(format!("{}", self.value.print()?)),
            _ => Ok(format!("{} {}", self.op, self.value.print()?)),
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
    type Err = util::ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();

        match s {
            "graduation-year" => Ok(Constant::GraduationYear),
            _ => Err(util::ParseError::UnknownCommand),
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

impl crate::rules::traits::PrettyPrint for Value {
    fn print(&self) -> Result<String, std::fmt::Error> {
        match &self {
            Value::String(s) => Ok(format!("{}", s)),
            Value::Integer(n) => Ok(format!("{}", n)),
            Value::Float(n) => Ok(format!("{:.2}", n)),
            Value::Bool(b) => Ok(format!("{}", b)),
            Value::Constant(s) => Ok(format!("{}", s)),
        }
    }
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
    type Err = util::ParseError;

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
    use crate::rules::given::action::Operator;

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
    fn deserialize_value_str() {
        let data = "FYW";
        let expected = Value::String("FYW".into());
        let actual: Value = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_value_int() {
        let data = "1";
        let expected = Value::Integer(1);
        let actual: Value = data.parse().unwrap();
        assert_eq!(actual, expected);

        let data = "100";
        let expected = Value::Integer(100);
        let actual: Value = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_value_float() {
        let data = "1.0";
        let expected = Value::Float(1.0);
        let actual: Value = data.parse().unwrap();
        assert_eq!(actual, expected);

        let data = "1.5";
        let expected = Value::Float(1.5);
        let actual: Value = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_value_bool() {
        let data = "true";
        let expected = Value::Bool(true);
        let actual: Value = data.parse().unwrap();
        assert_eq!(actual, expected);

        let data = "false";
        let expected = Value::Bool(false);
        let actual: Value = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_tagged_value_untagged() {
        let data = "FYW";
        let expected = TaggedValue {
            op: Operator::EqualTo,
            value: Value::String("FYW".into()),
        };
        let actual: TaggedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_tagged_value_eq() {
        let data = "= FYW";
        let expected = TaggedValue {
            op: Operator::EqualTo,
            value: Value::String("FYW".into()),
        };
        let actual: TaggedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_tagged_value_neq() {
        let data = "! FYW";
        let expected = TaggedValue {
            op: Operator::NotEqualTo,
            value: Value::String("FYW".into()),
        };
        let actual: TaggedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_tagged_value_gt() {
        let data = "> FYW";
        let expected = TaggedValue {
            op: Operator::GreaterThan,
            value: Value::String("FYW".into()),
        };
        let actual: TaggedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_tagged_value_gte() {
        let data = ">= FYW";
        let expected = TaggedValue {
            op: Operator::GreaterThanEqualTo,
            value: Value::String("FYW".into()),
        };
        let actual: TaggedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_tagged_value_lt() {
        let data = "< FYW";
        let expected = TaggedValue {
            op: Operator::LessThan,
            value: Value::String("FYW".into()),
        };
        let actual: TaggedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_tagged_value_lte() {
        let data = "<= FYW";
        let expected = TaggedValue {
            op: Operator::LessThanEqualTo,
            value: Value::String("FYW".into()),
        };
        let actual: TaggedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_wrapped_value() {
        let data = "FYW";
        let expected = WrappedValue::Single(TaggedValue {
            op: Operator::EqualTo,
            value: Value::String("FYW".into()),
        });
        let actual: WrappedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_wrapped_value_ne() {
        let data = "! FYW";
        let expected = WrappedValue::Single(TaggedValue {
            op: Operator::NotEqualTo,
            value: Value::String("FYW".into()),
        });
        let actual: WrappedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_wrapped_value_or_ne() {
        let data = "! FYW | = FYW";
        let expected = WrappedValue::Or([
            TaggedValue {
                op: Operator::NotEqualTo,
                value: Value::String("FYW".into()),
            },
            TaggedValue {
                op: Operator::EqualTo,
                value: Value::String("FYW".into()),
            },
        ]);
        let actual: WrappedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_wrapped_value_or_untagged() {
        let data = "FYW | FYW";
        let expected = WrappedValue::Or([
            TaggedValue {
                op: Operator::EqualTo,
                value: Value::String("FYW".into()),
            },
            TaggedValue {
                op: Operator::EqualTo,
                value: Value::String("FYW".into()),
            },
        ]);
        let actual: WrappedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_wrapped_value_and_untagged() {
        let data = "FYW & FYW";
        let expected = WrappedValue::And([
            TaggedValue {
                op: Operator::EqualTo,
                value: Value::String("FYW".into()),
            },
            TaggedValue {
                op: Operator::EqualTo,
                value: Value::String("FYW".into()),
            },
        ]);
        let actual: WrappedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn deserialize_wrapped_value_and_ne() {
        let data = "! FYW & = FYW";
        let expected = WrappedValue::And([
            TaggedValue {
                op: Operator::NotEqualTo,
                value: Value::String("FYW".into()),
            },
            TaggedValue {
                op: Operator::EqualTo,
                value: Value::String("FYW".into()),
            },
        ]);
        let actual: WrappedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    fn deserialize_test(s: &str) -> Option<Clause> {
        #[derive(Deserialize)]
        struct Wrapper(#[serde(deserialize_with = "deserialize_with")] Option<Clause>);

        let v: Wrapper = serde_yaml::from_str(s).unwrap();

        v.0
    }

    #[test]
    fn deserialize_wrapped_value_multiword_single_value() {
        let data = "St. Olaf College";
        let expected = WrappedValue::Single(TaggedValue {
            op: Operator::EqualTo,
            value: Value::String("St. Olaf College".into()),
        });
        let actual: WrappedValue = data.parse().unwrap();
        assert_eq!(actual, expected);
    }

    #[test]
    fn pretty_print_single_values() {
        use crate::rules::traits::PrettyPrint;

        let input: Clause = deserialize_test(&"{gereqs: FOL-C}").unwrap();
        let expected = "with the “FOL-C” general education attribute";
        assert_eq!(expected, input.print().unwrap());

        let input: Clause = deserialize_test(&"{semester: Interim}").unwrap();
        let expected = "during Interim semesters";
        assert_eq!(expected, input.print().unwrap());

        let input: Clause = deserialize_test(&"{semester: Fall}").unwrap();
        let expected = "during Fall semesters";
        assert_eq!(expected, input.print().unwrap());

        let input: Clause = deserialize_test(&"{year: '2012'}").unwrap();
        let expected = "during the 2012-13 academic year";
        assert_eq!(expected, input.print().unwrap());

        let input: Clause = deserialize_test(&"{institution: 'St. Olaf College'}").unwrap();
        let expected = "at St. Olaf College";
        assert_eq!(expected, input.print().unwrap());

        let input: Clause = deserialize_test(&"{department: MATH}").unwrap();
        let expected = "within the MATH department";
        assert_eq!(expected, input.print().unwrap());
    }

    #[test]
    fn pretty_print_multiple_values() {
        use crate::rules::traits::PrettyPrint;

        let input: Clause = deserialize_test(&"{semester: Fall | Interim}").unwrap();
        let expected = "during a Fall or Interim semester";
        assert_eq!(expected, input.print().unwrap());

        // TODO: fix this
        // let input: Clause = deserialize_test(&"{year: '2012 | 2013'}").unwrap();
        // let expected = "during the 2012-13 or 2013-14 academic year";
        // assert_eq!(expected, input.print().unwrap());

        let input: Clause = deserialize_test(&"{institution: 'Carleton College | St. Olaf College'}").unwrap();
        let expected = "at either Carleton College or St. Olaf College";
        assert_eq!(expected, input.print().unwrap());
    }

    #[test]
    fn pretty_print_negated_value() {
        use crate::rules::traits::PrettyPrint;

        let input: Clause = deserialize_test(&"{department: '! MATH'}").unwrap();
        let expected = "outside of the MATH department";
        assert_eq!(expected, input.print().unwrap());
    }
}
