#![warn(clippy::all)]

extern crate degreepath_parser;
use degreepath_parser::area_of_study::AreaOfStudy;
use degreepath_parser::requirement::Requirement;
use degreepath_parser::rules;
use degreepath_parser::rules::Rule;
use degreepath_parser::rules::{both, either, given};
use std::fmt;
use std::fmt::Write;

use degreepath_parser::rules::traits::PrettyPrint;

extern crate textwrap;

pub fn print(area: AreaOfStudy) -> Result<String, fmt::Error> {
	let mut w = String::new();

	use degreepath_parser::area_of_study::AreaType::{Concentration, Degree, Emphasis, Major, Minor};

	let leader = match area.area_type.clone() {
		Degree => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "degree".to_string();

			format!(
				"This is the set of requirements for the {catalog} “{area_name}” {area_type} from {institution}.",
				catalog = catalog,
				area_name = area_name,
				area_type = area_type,
				institution = institution
			)
		}
		Major { degree } => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "major".to_string();

			format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution)
		}
		Minor { degree } => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "minor".to_string();

			format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution)
		}
		Concentration { degree } => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "concentration".to_string();

			format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution)
		}
		Emphasis { degree, major } => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "area of emphasis".to_string();

			format!("This is the set of requirements for the {catalog} {for_degree} {for_major} major's “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, for_major = major, area_name = area_name, area_type = area_type, institution = institution)
		}
	};

	writeln!(&mut w, "{}", blockquote(&textwrap::fill(&leader, 78)))?;

	let area_type = match area.area_type.clone() {
		Degree => "degree",
		Major { .. } => "major",
		Minor { .. } => "minor",
		Concentration { .. } => "concentration",
		Emphasis { .. } => "area of emphasis",
	};

	if let Some(_attributes) = &area.attributes {
		writeln!(&mut w, "> todo: this area has custom attributes defined.\n")?;
	}

	if let Ok(what_to_do) = area.result.print() {
		writeln!(
			&mut w,
			"{}",
			&format!(
				"For this {area_type}, you must complete {what_to_do}.",
				area_type = area_type,
				what_to_do = what_to_do
			)
		)?;
	}

	let active_children = collect_active_requirements_from_area(&area.clone());
	let requirements: Vec<String> = active_children
		.iter()
		.flat_map(|(name, r)| print_requirement(name, &r.clone(), 1))
		.collect();

	for s in requirements {
		write!(&mut w, "\n{}", s)?;
	}

	Ok(w)
}

fn blockquote(text: &str) -> String {
	textwrap::indent(&text, "> ")
}

fn print_requirement(name: &str, req: &Requirement, level: usize) -> Result<String, fmt::Error> {
	let mut w = String::new();

	writeln!(&mut w, "{} {}", "#".repeat(level), name)?;

	if let Some(message) = &req.message {
		let message = format!("Note: {}", message);
		writeln!(&mut w, "{}", blockquote(&textwrap::fill(&message, 78)))?;
	}

	if req.department_audited {
		let message = format!("For this requirement, you must have done what the note says. The Department must certify that you have done so.");
		writeln!(&mut w, "{}", &textwrap::fill(&message, 80))?;
	}

	if req.contract {
		let message = format!("This section is a Contract section. You must talk to the Department to fill out, file, and update the Contract.");
		writeln!(&mut w, "{}", &textwrap::fill(&message, 80))?;
	}

	if !req.save.is_empty() {
		for block in req.save.clone() {
			writeln!(&mut w, "{}", block.print()?)?;
		}
	}

	let active_children = collect_active_requirements(&req);

	if let Some(result) = &req.result {
		if let Ok(mut what_to_do) = result.print() {
			let kind = match req.requirements.len() {
				0 => "requirement",
				_ => "section",
			};

			// todo: remove this hack for adding periods to the end of inlined requirements
			if !what_to_do.contains("\n- ") {
				what_to_do += ".";
			}

			writeln!(
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

	let requirements: Vec<String> = active_children
		.iter()
		.flat_map(|(name, r)| print_requirement(name, &r.clone(), level + 1))
		.collect();

	for s in requirements {
		write!(&mut w, "{}", s)?;
	}

	if !w.ends_with("\n") {
		writeln!(&mut w, "")?;
	}

	Ok(w)
}

fn collect_active_requirements_from_area(area: &AreaOfStudy) -> Vec<(String, Requirement)> {
	let refs = get_requirement_references_from_rule(&area.result);

	refs.iter()
		.map(|r| {
			(
				r.requirement.clone(),
				area.requirements
					.get(&r.requirement)
					.expect(&format!("{} was not found in the requirements list", r.requirement))
					.clone(),
			)
		})
		.collect()
}

fn collect_active_requirements(req: &Requirement) -> Vec<(String, Requirement)> {
	let refs = match &req.result {
		Some(rule) => get_requirement_references_from_rule(rule),
		None => vec![],
	};

	refs.iter()
		.map(|r| {
			(
				r.requirement.clone(),
				req.requirements
					.get(&r.requirement)
					.expect(&format!("{} was not found in the requirements list", r.requirement))
					.clone(),
			)
		})
		.collect()
}

fn get_requirement_references_from_rule(rule: &Rule) -> Vec<rules::requirement::Rule> {
	use degreepath_parser::rules::Rule::*;

	match rule {
		CountOf(rule) => rule
			.of
			.iter()
			.flat_map(|r| get_requirement_references_from_rule(r))
			.collect::<Vec<_>>(),
		Requirement(rule) => vec![rule.clone()],
		Course(_) => vec![],
		Both(both::Rule { both: pair }) | Either(either::Rule { either: pair }) => {
			let pair = pair.clone();
			vec![pair.0, pair.1]
				.iter()
				.flat_map(|r| get_requirement_references_from_rule(r))
				.collect::<Vec<_>>()
		}
		Given(rule) => match &rule.given {
			given::Given::TheseRequirements { requirements } => requirements.clone(),
			_ => vec![],
		},
		Do(_) => vec![],
	}
}
