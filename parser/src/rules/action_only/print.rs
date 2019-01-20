use super::*;
use crate::traits::print;

impl print::Print for Rule {
	fn print(&self) -> print::Result {
		use crate::action::Operator;
		use std::fmt::Write;

		let mut output = String::new();
		let action = &self.action;

		match (&action.lhs, &action.op, &action.rhs) {
			(lhs, Some(op), Some(rhs)) => {
				let op = match op {
					Operator::LessThan => "less than",
					Operator::LessThanEqualTo => "less most or equal to",
					Operator::EqualTo => "equal to",
					Operator::GreaterThan => "greater than",
					Operator::GreaterThanEqualTo => "greater than or equal to",
					Operator::NotEqualTo => "not equal to",
				};

				write!(
					&mut output,
					"ensure that the computed result of the subset “{}” is {} the computed result of the subset “{}”",
					lhs, op, rhs
				)?;
			}
			_ => panic!("invalid standalone do-rule"),
		}

		Ok(output)
	}
}
