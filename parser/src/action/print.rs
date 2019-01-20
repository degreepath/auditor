use super::{Action, Command, Operator, Value};
use crate::traits::print;
use std::fmt::Write;

impl print::Print for Action {
	fn print(&self) -> print::Result {
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
