use std::error::Error;
use std::fmt;
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    InvalidAction,
    UnknownOperator,
    InvalidValue,
    UnknownCommand,
    InvalidVariableName,
}

impl fmt::Display for ParseError {
    fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
        fmt.write_str(self.description())
    }
}

impl Error for ParseError {
    fn description(&self) -> &str {
        "invalid do: command syntax"
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Action {
    pub lhs: Value,
    pub op: Option<Operator>,
    pub rhs: Option<Value>,
}

impl FromStr for Action {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let splitted: Vec<_> = s.split_whitespace().collect();

        match splitted.as_slice() {
            [command] => {
                let lhs = command.parse::<Value>()?;

                Ok(Action {
                    lhs,
                    op: None,
                    rhs: None,
                })
            }
            [left, operator, right] => {
                let lhs = left.parse::<Value>()?;
                let op = operator.parse::<Operator>()?;
                let rhs = right.parse::<Value>()?;

                Ok(Action {
                    lhs,
                    op: Some(op),
                    rhs: Some(rhs),
                })
            }
            _ => return Err(ParseError::InvalidAction),
        }
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Operator {
    LessThan,
    LessThanEqualTo,
    EqualTo,
    GreaterThan,
    GreaterThanEqualTo,
}

impl FromStr for Operator {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.as_ref() {
            "<" => Ok(Operator::LessThan),
            "<=" => Ok(Operator::LessThanEqualTo),
            "=" => Ok(Operator::EqualTo),
            ">" => Ok(Operator::GreaterThan),
            ">=" => Ok(Operator::GreaterThanEqualTo),
            _ => Err(ParseError::UnknownOperator),
        }
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Value {
    Command(Command),
    Variable(NamedVariable),
    String(String),
    Integer(u64),
    Float(f64),
}

impl FromStr for Value {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if let Ok(var) = s.parse::<NamedVariable>() {
            return Ok(Value::Variable(var));
        }

        if let Ok(num) = s.parse::<u64>() {
            return Ok(Value::Integer(num));
        }

        if let Ok(num) = s.parse::<f64>() {
            return Ok(Value::Float(num));
        }

        if let Ok(command) = s.parse::<Command>() {
            return Ok(Value::Command(command));
        }

        return Err(ParseError::InvalidValue);
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Command {
    Count,
    Sum,
    Average,
    Minimum,
    Maximum,
    Difference,
}

impl FromStr for Command {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();

        match s {
            "count" => Ok(Command::Count),
            "sum" => Ok(Command::Sum),
            "average" => Ok(Command::Average),
            "minimum" => Ok(Command::Minimum),
            "maximum" => Ok(Command::Maximum),
            "difference" => Ok(Command::Difference),
            _ => Err(ParseError::UnknownCommand),
        }
    }
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct NamedVariable {
    pub name: String,
}

impl NamedVariable {
    pub fn new(name: &str) -> NamedVariable {
        NamedVariable {
            name: name.to_string(),
        }
    }
}

impl FromStr for NamedVariable {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();

        match s.starts_with("$") {
            true => Ok(NamedVariable::new(&s.replacen("$", "", 1))),
            false => Err(ParseError::InvalidVariableName),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn count_gte_6() {
        let actual: Action = "count >= 6".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Count),
            op: Some(Operator::GreaterThanEqualTo),
            rhs: Some(Value::Integer(6)),
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn count_eq_1() {
        let actual: Action = "count = 1".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Count),
            op: Some(Operator::EqualTo),
            rhs: Some(Value::Integer(1)),
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn average_gte_2_0() {
        let actual: Action = "average >= 2.0".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Average),
            op: Some(Operator::GreaterThanEqualTo),
            rhs: Some(Value::Float(2.0)),
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn average_gte_2() {
        let actual: Action = "average >= 2".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Average),
            op: Some(Operator::GreaterThanEqualTo),
            rhs: Some(Value::Integer(2)),
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn sum_eq_6() {
        let actual: Action = "sum = 6".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Sum),
            op: Some(Operator::EqualTo),
            rhs: Some(Value::Integer(6)),
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn sum_gte_1_5() {
        let actual: Action = "sum >= 1.5".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Sum),
            op: Some(Operator::GreaterThanEqualTo),
            rhs: Some(Value::Float(1.5)),
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn difference_lte_1() {
        let actual: Action = "difference <= 1".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Difference),
            op: Some(Operator::LessThanEqualTo),
            rhs: Some(Value::Integer(1)),
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn maximum() {
        let actual: Action = "maximum".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Maximum),
            op: None,
            rhs: None,
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn minimum() {
        let actual: Action = "minimum".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Command(Command::Minimum),
            op: None,
            rhs: None,
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    fn var_lt_var() {
        let actual: Action = "$first_btst < $last_ein".parse().unwrap();

        let expected_struct = Action {
            lhs: Value::Variable(NamedVariable::new("first_btst")),
            op: Some(Operator::LessThan),
            rhs: Some(Value::Variable(NamedVariable::new("last_ein"))),
        };

        assert_eq!(actual, expected_struct);
    }

    #[test]
    #[should_panic]
    fn invalid_flipped_operator() {
        "a => b".parse::<Action>().unwrap();
    }
}
