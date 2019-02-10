use super::*;
use crate::traits::print;

impl print::Print for Rule {
	fn print(&self) -> print::Result {
		use crate::rules::Rule::{Course, Requirement};
		use std::fmt::Write;

		let mut output = String::new();

		let pair = self.both.clone();

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
					"complete both the {} and {} requirements",
					a.print()?,
					b.print()?
				)?;
			}
			(Course(a), Course(b)) => {
				write!(&mut output, "take both {} and {}", a.print()?, b.print()?)?;
			}
			(Requirement(a), Course(b)) => {
				write!(
					&mut output,
					"complete the {} requirement and take {}",
					a.print()?,
					b.print()?
				)?;
			}
			(Course(a), Requirement(b)) => {
				write!(
					&mut output,
					"take {} and complete the {} requirement",
					a.print()?,
					b.print()?
				)?;
			}
			(Course(a), b) => {
				write!(&mut output, "both take {} and {}", a.print()?, b.print()?)?;
			}
			(Requirement(a), b) => {
				write!(
					&mut output,
					"both complete the {} requirement and {}",
					a.print()?,
					b.print()?
				)?;
			}
			(a, Course(b)) => {
				write!(&mut output, "both {} and take {}", a.print()?, b.print()?)?;
			}
			(a, Requirement(b)) => {
				write!(
					&mut output,
					"both {} and complete the {} requirement",
					a.print()?,
					b.print()?
				)?;
			}
			(a, b) => {
				let a = a.print_indented(1)?;
				let b = b.print_indented(1)?;

				write!(&mut output, "both:\n\n- {}\n\n- and {}", a, b)?;
			}
		};

		Ok(output)
	}
}
