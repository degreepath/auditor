use super::Value;
use crate::action::Operator;
use crate::traits::print;
use crate::util;
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
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
				let splitted: Vec<&str> = s.split_whitespace().collect();

				let splitted = if let Some((first, rest)) = splitted.split_first() {
					vec![first.to_string(), rest.join(" ")]
				} else {
					vec![]
				};

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

impl print::Print for TaggedValue {
	fn print(&self) -> print::Result {
		match &self.op {
			Operator::EqualTo => self.value.print(),
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
