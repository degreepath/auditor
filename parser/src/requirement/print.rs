use super::*;
use crate::traits::print::Print;
use std::fmt::Write;

impl Requirement {
	pub fn print(&self, name: &str, level: usize) -> Result<String, std::fmt::Error> {
		let mut w = String::new();

		writeln!(&mut w, "{} {}", "#".repeat(level), name)?;

		if let Some(message) = &self.message {
			let message = format!("Note: {}", message);
			let message = message
				.lines()
				.map(|l| format!("> {}", l))
				.collect::<Vec<_>>()
				.join("\n");

			writeln!(&mut w, "{}\n", message)?;
		}

		if self.department_audited {
			let message = "For this requirement, you must have done what the note says. The Department must certify that you have done so.";
			writeln!(&mut w, "{}\n", message)?;
		}

		if self.registrar_audited {
			let message = "For this requirement, you must have done what the note says. This must be verified and set by the registrar.";
			writeln!(&mut w, "{}\n", message)?;
		}

		if self.contract {
			let message = "This section is a Contract section. You must talk to the Department to fill out, file, and update the Contract.";
			writeln!(&mut w, "{}\n", message)?;
		}

		if !self.save.is_empty() {
			for block in self.save.clone() {
				writeln!(&mut w, "{}", block.print()?)?;
			}
		}

		if let Some(result) = &self.result {
			if let Ok(mut what_to_do) = result.print() {
				let kind = match self.requirements.len() {
					0 => "requirement",
					_ => "section",
				};

				// todo: remove this hack for adding periods to the end of inlined requirements
				if !what_to_do.contains('\n') {
					what_to_do += ".";
				}

				if !what_to_do.ends_with('\n') {
					what_to_do += "\n";
				}

				let what_to_do = format!("For this {}, you must {}", kind, what_to_do);
				writeln!(&mut w, "{}", &what_to_do)?;
			}
		}

		for (name, req) in &self.requirements {
			write!(&mut w, "{}", req.print(&name, level + 1)?)?;
		}

		if !w.ends_with('\n') {
			writeln!(&mut w)?;
		}

		Ok(w)
	}
}
