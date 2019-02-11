use super::{Action, Command, Operator, Value};
use crate::util::ParseError;
use std::str::FromStr;

impl FromStr for Action {
	type Err = ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		let collected = split_action_str(&s);

		match collected.as_slice() {
			[command] => {
				let lhs = command.parse::<Command>()?;

				Ok(Action {
					lhs,
					op: None,
					rhs: None,
				})
			}
			[left, operator, right] => {
				let lhs = left.parse::<Command>()?;
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

fn split_action_str(s: &str) -> Vec<String> {
	let mut in_str = false;
	let mut collected: Vec<String> = vec![];
	let mut current = String::new();
	for ch in s.chars() {
		if ch == '"' {
			in_str = !in_str;
			continue;
		}

		if in_str {
			current += &ch.to_string();
			continue;
		}

		if ch.is_whitespace() {
			if !current.is_empty() {
				collected.push(current.trim().to_string());
				current = String::new();
			}

			continue;
		} else {
			current += &ch.to_string();
		}
	}

	if !current.is_empty() {
		collected.push(current.trim().to_string());
	}

	collected
}

#[cfg(test)]
mod tests {
	use super::*;

	#[test]
	fn split_action_str_test() {
		assert_eq!(split_action_str("count > 6"), vec!["count", ">", "6"]);
		assert_eq!(split_action_str(r#""a" > 6"#), vec!["a", ">", "6"]);
		assert_eq!(split_action_str(r#""a space" > 6"#), vec!["a space", ">", "6"]);
		assert_eq!(split_action_str(r#""a space"     >  6"#), vec!["a space", ">", "6"]);
		assert_eq!(
			split_action_str(r#""a space"     >  "b space""#),
			vec!["a space", ">", "b space"]
		);
		assert_eq!(
			split_action_str(r#""a space"     >  "b  space""#),
			vec!["a space", ">", "b  space"]
		);

		assert_eq!(
			split_action_str(r#"   "a space"     >  "b  space" "#),
			vec!["a space", ">", "b  space"]
		);
	}
}
