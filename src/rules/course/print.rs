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

		if let Some(lab) = self.lab {
			if lab {
				match &annotations {
					Some(ann) => {
						annotations = Some(format!("Lab; {}", ann));
					}
					None => {
						annotations = Some("Lab".to_string());
					}
				}
			}
		}

		match (&self.grade, &annotations) {
			(Some(grade), Some(ann)) => annotations = Some(format!("{}; {} or higher", ann, String::from(grade))),
			(Some(grade), None) => annotations = Some(format!("{} or higher", String::from(grade))),
			_ => (),
		}

		if let Some(annotations) = annotations {
			write!(&mut output, " ({})", annotations)?;
		}

		Ok(output)
	}
}
