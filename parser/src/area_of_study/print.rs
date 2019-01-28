use super::*;
use crate::traits::print::Print;
use std::fmt::Write;

impl AreaOfStudy {
	pub fn print(&self) -> Result<String, std::fmt::Error> {
		let mut w = String::new();

		use AreaType::{Concentration, Degree, Emphasis, Major, Minor};

		let area_type = match &self.area_type {
			Degree => "degree",
			Major { .. } => "major",
			Minor { .. } => "minor",
			Concentration { .. } => "concentration",
			Emphasis { .. } => "area of emphasis",
		};

		let leader = {
			let catalog = &self.catalog;
			let area_name = &self.area_name;
			let institution = &self
				.institution
				.clone()
				.unwrap_or_else(|| "St. Olaf College".to_string());

			match &self.area_type {
                Degree => format!("This is the set of requirements for the {catalog} “{area_name}” {area_type} from {institution}.", catalog = catalog, area_name = area_name, area_type = area_type, institution = institution),
                Major { degree } => format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution),
                Minor { degree } => format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution),
                Concentration { degree } => format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution),
                Emphasis { degree, major } => format!("This is the set of requirements for the {catalog} {for_degree} {for_major} major's “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, for_major = major, area_name = area_name, area_type = area_type, institution = institution),
            }
		};

		writeln!(&mut w, "> {}\n", leader)?;

		writeln!(&mut w, "# {}", &self.area_name)?;

		if let Some(_attributes) = &self.attributes {
			writeln!(&mut w, "> todo: this area has custom attributes defined.\n")?;
		}

		if let Ok(mut what_to_do) = self.result.print() {
			// todo: remove this hack for adding periods to the end of inlined requirements
			if !what_to_do.contains('\n') {
				what_to_do += ".";
			}

			if !what_to_do.ends_with('\n') {
				what_to_do += "\n";
			}

			let what_to_do = format!("For this {}, you must {}", area_type, what_to_do);
			write!(&mut w, "{}", &what_to_do)?;
		}

		for (name, req) in &self.requirements {
			write!(&mut w, "\n{}", req.print(&name, 2)?)?;
		}

		Ok(w)
	}
}
