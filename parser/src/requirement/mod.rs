use crate::rules::Rule;
use crate::save::SaveBlock;
use crate::util;
use indexmap::IndexMap;

#[cfg(test)]
mod tests;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Requirement {
	#[serde(default)]
	pub message: Option<String>,
	#[serde(default = "util::serde_false")]
	pub department_audited: bool,
	#[serde(default)]
	pub result: Option<Rule>,
	#[serde(default = "util::serde_false")]
	pub contract: bool,
	#[serde(default)]
	pub save: Vec<SaveBlock>,
	#[serde(default)]
	pub requirements: IndexMap<String, Requirement>,
}

pub mod print {
	use super::*;
	use crate::traits::print::Print;
	use std::fmt::Write;

	impl Requirement {
		pub fn print(&self, name: &str, level: usize) -> Result<String, std::fmt::Error> {
			let mut w = String::new();

			writeln!(&mut w, "{} {}", "#".repeat(level), name)?;

			if let Some(message) = &self.message {
				let message = format!("> Note: {}", message);
				writeln!(&mut w, "{}", message)?;
			}

			if self.department_audited {
				let message = "For this requirement, you must have done what the note says. The Department must certify that you have done so.";
				writeln!(&mut w, "{}", message)?;
			}

			if self.contract {
				let message = "This section is a Contract section. You must talk to the Department to fill out, file, and update the Contract.";
				writeln!(&mut w, "{}", message)?;
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
					if !what_to_do.contains("\n") {
						what_to_do += ".";
					}

					if !what_to_do.ends_with("\n") {
						what_to_do += "\n";
					}

					write!(
						&mut w,
						"{}\n",
						&format!(
							"For this {kind}, you must {what_to_do}",
							kind = kind,
							what_to_do = what_to_do
						),
					)?;
				}
			}

			let requirements: Vec<String> = self
				.requirements
				.iter()
				.flat_map(|(name, r)| r.print(name, level + 1))
				.collect();

			for s in requirements {
				write!(&mut w, "{}", s)?;
			}

			if !w.ends_with("\n") {
				writeln!(&mut w, "")?;
			}

			Ok(w)
		}
	}
}
