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

		let mut annotations = match (&self.term, self.year, &self.semester) {
			(Some(term), None, None) => Some(util::pretty_term(&term)),
			(None, Some(year), None) => Some(util::expand_year(year, "dual")),
			(None, None, Some(semester)) => Some(semester.clone()),
			(None, Some(year), Some(semester)) => Some(format!("{} {}", semester, util::expand_year(year, "short"))),
			(Some(_), Some(_), _) | (Some(_), _, Some(_)) => unimplemented!("courses with term+year or term+semester"),
			(None, None, None) => None,
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

		match (self.international, &annotations) {
			(Some(intl), Some(ant)) if intl => {
				annotations = Some(format!("International; {}", ant));
			}
			(Some(intl), None) if intl => {
				annotations = Some("International".to_string());
			}
			_ => (),
		}

		if let Some(annotations) = annotations {
			write!(&mut output, " ({})", annotations)?;
		}

		Ok(output)
	}
}
