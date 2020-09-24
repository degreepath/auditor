use serde::{Deserialize, Serialize};
use std::fmt::Display;

#[derive(Serialize, Deserialize, Debug, Clone, Eq, PartialEq)]
pub enum Operator {
    NotEqualTo,
    EqualTo,
    In,
    NotIn,
    LessThan,
    LessThanOrEqualTo,
    GreaterThan,
    GreaterThanOrEqualTo,
}

impl Display for Operator {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let symbol = match self {
            Operator::LessThan => "<",
            Operator::LessThanOrEqualTo => "≤",
            Operator::GreaterThan => ">",
            Operator::GreaterThanOrEqualTo => "≥",
            Operator::EqualTo => "==",
            Operator::NotEqualTo => "!=",
            Operator::In => "∈",
            Operator::NotIn => "∉",
        };

        f.write_str(symbol)
    }
}
