use super::{Action, Command, Operator, Value};
use crate::traits::print;
use std::fmt::Write;

impl print::Print for Action {
	fn print(&self) -> print::Result {
		let mut output = String::new();

		match (&self.lhs, &self.op, &self.rhs) {
			(Value::String(s), Some(op), Some(val)) if *s == Command::Count => {
				write!(&mut output, "{} {}", op.print()?, val.print()?)?
			}
			(Value::String(s), Some(op), Some(val)) if *s == Command::Sum => {
				write!(&mut output, "{} {}", op.print()?, val.print()?)?
			}
			(Value::String(s), Some(Operator::GreaterThan), Some(val)) if *s == Command::Average => {
				write!(&mut output, "above {}", val.print()?)?
			}
			(Value::String(s), Some(Operator::GreaterThanEqualTo), Some(val)) if *s == Command::Average => {
				write!(&mut output, "at or above {}", val.print()?)?
			}
			_ => unimplemented!(
				"in Action's printer, the combo of `{:?}`, `{:?}`, and `{:?}`",
				&self.lhs,
				&self.op,
				&self.rhs
			),
		};

		Ok(output)
	}
}
