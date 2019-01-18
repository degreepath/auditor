use super::Rule;
use crate::rules::traits::PrettyPrint;
use std::fmt;

impl PrettyPrint for Rule {
	fn print(&self) -> Result<String, fmt::Error> {
		use std::fmt::Write;
		let mut output = String::new();

		write!(&mut output, "“{}”", self.requirement)?;

		if self.optional == true {
			write!(&mut output, " (optional)")?;
		}

		Ok(output)
	}
}
