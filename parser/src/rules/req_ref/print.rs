use super::*;
use crate::traits::print;

impl print::Print for Rule {
	fn print(&self) -> print::Result {
		use std::fmt::Write;
		let mut output = String::new();

		write!(&mut output, "“{}”", self.requirement)?;

		if self.optional == true {
			write!(&mut output, " (optional)")?;
		}

		Ok(output)
	}
}
