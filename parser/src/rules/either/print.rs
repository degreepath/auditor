use super::*;
use crate::rules::traits::PrettyPrint;
use std::fmt;

impl PrettyPrint for Rule {
	fn print(&self) -> Result<String, fmt::Error> {
		use crate::rules::Rule::{Course, Requirement};
		use std::fmt::Write;

		let mut output = String::new();

		let pair = self.either.clone();

		if self.has_save_rule() {
			write!(&mut output, "do both of the following:\n\n")?;
			writeln!(&mut output, "- {}", (*pair.0).print()?)?;
			writeln!(&mut output, "- {}", (*pair.1).print()?)?;
			return Ok(output);
		}

		match (*pair.0, *pair.1) {
			(Requirement(a), Requirement(b)) => {
				write!(
					&mut output,
					"complete either the {} or {} requirement",
					a.print()?,
					b.print()?
				)?;
			}
			(Course(a), Course(b)) => {
				write!(&mut output, "take either {} or {}", a.print()?, b.print()?)?;
			}
			(Requirement(a), Course(b)) => {
				write!(
					&mut output,
					"complete the {} requirement or take {}",
					a.print()?,
					b.print()?
				)?;
			}
			(Course(a), Requirement(b)) => {
				write!(
					&mut output,
					"take {} or complete the {} requirement",
					a.print()?,
					b.print()?
				)?;
			}
			(Course(a), b) => {
				write!(&mut output, "either take {} or {}", a.print()?, b.print()?)?;
			}
			(Requirement(a), b) => {
				write!(
					&mut output,
					"either complete the {} requirement or {}",
					a.print()?,
					b.print()?
				)?;
			}
			(a, Course(b)) => {
				write!(&mut output, "either {} or take {}", a.print()?, b.print()?)?;
			}
			(a, Requirement(b)) => {
				write!(
					&mut output,
					"either {} or complete the {} requirement",
					a.print()?,
					b.print()?
				)?;
			}
			(a, b) => {
				write!(&mut output, "either:\n\n- {}\n\n- or {}", a.print()?, b.print()?)?;
			}
		};

		Ok(output)
	}
}
