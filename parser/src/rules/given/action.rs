use crate::util;
use crate::util::ParseError;
use serde::de::{Deserialize, Deserializer};
use serde::ser::{Serialize, Serializer};
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Deserialize, Clone)]
pub struct Action {
	pub lhs: Value,
	pub op: Option<Operator>,
	pub rhs: Option<Value>,
}

impl Action {
	pub fn should_pluralize(&self) -> bool {
		match &self.rhs {
			Some(Value::Integer(n)) if *n == 1 => false,
			Some(Value::Integer(_)) => true,
			Some(Value::Float(f)) if *f == 1.0 => false,
			Some(Value::Float(_)) => true,
			_ => false,
		}
	}
}

impl crate::rules::traits::PrettyPrint for Action {
	fn print(&self) -> Result<String, std::fmt::Error> {
		use std::fmt::Write;

		let mut output = String::new();

		match (&self.lhs, &self.op, &self.rhs) {
			(Value::Command(Command::Count), Some(op), Some(val)) => {
				write!(&mut output, "{} {}", op.print()?, val.print()?)?
			}
			(Value::Command(Command::Sum), Some(op), Some(val)) => {
				write!(&mut output, "{} {}", op.print()?, val.print()?)?
			}
			(Value::Command(Command::Average), Some(Operator::GreaterThan), Some(val)) => {
				write!(&mut output, "above {}", val.print()?)?
			}
			(Value::Command(Command::Average), Some(Operator::GreaterThanEqualTo), Some(val)) => {
				write!(&mut output, "at or above {}", val.print()?)?
			}
			_ => unimplemented!(),
		};

		Ok(output)
	}
}

impl Serialize for Action {
	fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
	where
		S: Serializer,
	{
		serializer.serialize_str(&format!("{}", &self))
	}
}

impl fmt::Display for Action {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Action {
				lhs,
				rhs: None,
				op: None,
			} => write!(f, "{}", lhs),
			Action {
				lhs,
				rhs: Some(rhs),
				op: Some(op),
			} => write!(f, "{} {} {}", lhs, op, rhs),
			_ => Err(fmt::Error),
		}
	}
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
			_ => Err(ParseError::InvalidAction),
		}
	}
}

pub fn option_action<'de, D>(deserializer: D) -> Result<Option<Action>, D::Error>
where
	D: Deserializer<'de>,
{
	#[derive(Deserialize)]
	struct Wrapper(#[serde(deserialize_with = "util::string_or_struct_parseerror")] Action);

	let v = Option::deserialize(deserializer)?;
	Ok(v.map(|Wrapper(a)| a))
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Operator {
	LessThan,
	LessThanEqualTo,
	EqualTo,
	GreaterThan,
	GreaterThanEqualTo,
	NotEqualTo,
}

impl crate::rules::traits::PrettyPrint for Operator {
	fn print(&self) -> Result<String, std::fmt::Error> {
		Ok(match &self {
			Operator::LessThan => "fewer than",
			Operator::LessThanEqualTo => "at most",
			Operator::EqualTo => "exactly",
			Operator::GreaterThan => "more than",
			Operator::GreaterThanEqualTo => "at least",
			Operator::NotEqualTo => "not",
		}
		.to_string())
	}
}

impl FromStr for Operator {
	type Err = ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		match s {
			"<" => Ok(Operator::LessThan),
			"<=" => Ok(Operator::LessThanEqualTo),
			"=" => Ok(Operator::EqualTo),
			">" => Ok(Operator::GreaterThan),
			">=" => Ok(Operator::GreaterThanEqualTo),
			"!" => Ok(Operator::NotEqualTo),
			_ => Err(ParseError::UnknownOperator),
		}
	}
}

impl fmt::Display for Operator {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Operator::LessThan => write!(f, "<"),
			Operator::LessThanEqualTo => write!(f, "<="),
			Operator::EqualTo => write!(f, "="),
			Operator::GreaterThan => write!(f, ">"),
			Operator::GreaterThanEqualTo => write!(f, ">="),
			Operator::NotEqualTo => write!(f, "!"),
		}
	}
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Value {
	Command(Command),
	Variable(String),
	String(String),
	Integer(u64),
	Float(f64),
}

impl FromStr for Value {
	type Err = ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		if s.starts_with('$') {
			return Ok(Value::Variable(s.to_string()));
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

		Err(ParseError::InvalidValue)
	}
}

impl fmt::Display for Value {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Value::Command(cmd) => write!(f, "{}", cmd),
			Value::Variable(name) => write!(f, "{}", name),
			Value::String(v) => write!(f, "{}", v),
			Value::Integer(v) => write!(f, "{}", v),
			Value::Float(v) => write!(f, "{:.2}", v),
		}
	}
}

impl crate::rules::traits::PrettyPrint for Value {
	fn print(&self) -> Result<String, std::fmt::Error> {
		match &self {
			Value::Command(_) => unimplemented!(),
			Value::Variable(name) => Ok(name.to_string()),
			Value::String(v) => Ok(format!("“{}”", v)),
			Value::Integer(n) => Ok(match n {
				0 => "zero".to_string(),
				1 => "one".to_string(),
				2 => "two".to_string(),
				3 => "three".to_string(),
				4 => "four".to_string(),
				5 => "five".to_string(),
				6 => "six".to_string(),
				7 => "seven".to_string(),
				8 => "eight".to_string(),
				9 => "nine".to_string(),
				10 => "ten".to_string(),
				_ => format!("{}", n),
			}),
			Value::Float(v) => Ok(format!("{:.2}", v)),
		}
	}
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Command {
	Count,
	Sum,
	Average,
	Minimum,
	Maximum,
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
			_ => Err(ParseError::UnknownCommand),
		}
	}
}

impl fmt::Display for Command {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		match &self {
			Command::Count => write!(f, "count"),
			Command::Sum => write!(f, "sum"),
			Command::Average => write!(f, "average"),
			Command::Minimum => write!(f, "minimum"),
			Command::Maximum => write!(f, "maximum"),
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
			lhs: Value::Variable(String::from("$first_btst")),
			op: Some(Operator::LessThan),
			rhs: Some(Value::Variable(String::from("$last_ein"))),
		};

		assert_eq!(actual, expected_struct);
	}

	#[test]
	#[should_panic]
	fn invalid_flipped_operator() {
		"a => b".parse::<Action>().unwrap();
	}
}
