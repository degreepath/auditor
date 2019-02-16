use super::*;
use crate::traits::print;
use crate::util;

impl print::Print for Rule {
	fn print(&self) -> print::Result {
		use std::fmt::Write;
		let mut output = String::new();

		write!(&mut output, "{}", self.course)?;

		if let Some(section) = &self.section {
			write!(&mut output, "{}", section)?;
		}

		let mut annotations = match (self.year, &self.semester) {
			(Some(year), None) => Some(util::expand_year(year, "dual")),
			(None, Some(semester)) => Some(semester.to_string()),
			(Some(year), Some(semester)) => Some(format!("{} {}", semester, util::expand_year(year, "short"))),
			(None, None) => None,
		};

		match (self.lab, &annotations) {
			(Some(lab), Some(ant)) if lab => {
				annotations = Some(format!("Lab; {}", ant));
			}
			(Some(lab), None) if lab => {
				annotations = Some("Lab".to_string());
			}
			_ => (),
		}

		if let Some(annotations) = annotations {
			write!(&mut output, " ({})", annotations)?;
		}

		Ok(output)
	}
}
