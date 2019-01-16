#![warn(clippy::all)]

extern crate degreepath_parser;
use degreepath_parser::area_of_study::AreaOfStudy;
use degreepath_parser::requirement::Requirement;
use degreepath_parser::rules;
use degreepath_parser::rules::given::{action, filter};
use degreepath_parser::rules::Rule;
use degreepath_parser::rules::{both, either, given};
// use degreepath_parser::save;
use degreepath_parser::save::SaveBlock;
use std::fmt;
use std::fmt::Write;

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

			#[cfg_attr(rustfmt, rustfmt_skip)]
            format!("This is the set of requirements for the {catalog} “{area_name}” {area_type} from {institution}.", catalog = catalog, area_name = area_name, area_type = area_type, institution = institution )
		}
		Major { degree } => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "major".to_string();

			#[cfg_attr(rustfmt, rustfmt_skip)]
            format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution)
		}
		Minor { degree } => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "minor".to_string();

			#[cfg_attr(rustfmt, rustfmt_skip)]
            format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution)
		}
		Concentration { degree } => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "concentration".to_string();

			#[cfg_attr(rustfmt, rustfmt_skip)]
            format!("This is the set of requirements for the {catalog} {for_degree} “{area_name}” {area_type} from {institution}.", catalog = catalog, for_degree = degree, area_name = area_name, area_type = area_type, institution = institution)
		}
		Emphasis { degree, major } => {
			let catalog = area.catalog.clone();
			let area_name = area.area_name.clone();
			let institution = "St. Olaf College";
			let area_type = "area of emphasis".to_string();

			#[cfg_attr(rustfmt, rustfmt_skip)]
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

	if let Ok(what_to_do) = summarize_result(&area.result) {
		writeln!(
			&mut w,
			"{}",
			textwrap::fill(
				&format!(
					"For this {area_type}, you must complete {what_to_do}.",
					area_type = area_type,
					what_to_do = what_to_do
				),
				80,
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

fn print_rule_as_title(rule: &Rule) -> Result<String, fmt::Error> {
	match rule {
		Rule::Requirement(rules::requirement::Rule { requirement, .. }) => Ok(format!("“{}”", requirement)),
		Rule::Course(rules::course::Rule { course, .. }) => Ok(course.to_string()),
		Rule::Either(rules::either::Rule { either: pair }) | Rule::Both(rules::both::Rule { both: pair }) => {
			let a = summarize_result(&pair.0.clone())?;
			let b = summarize_result(&pair.1.clone())?;
			Ok(format!("{}, {}", a, b))
		}
		Rule::Given(given::Rule { .. }) => Ok("given blah".to_string()),
		Rule::Do(rules::action::Rule { .. }) => Ok("do blah".to_string()),
		Rule::CountOf(rules::count_of::Rule { of, count }) => Ok(format!(
			"{} {}",
			count,
			of.iter()
				.map(|r| print_rule_as_title(&r.clone()).unwrap_or("error!!!".to_string()))
				.collect::<Vec<String>>()
				.join(" • ")
		)),
	}
}

fn print_requirement(name: &str, req: &Requirement, level: usize) -> Result<String, fmt::Error> {
	let mut w = String::new();

	writeln!(&mut w, "{} {}", "#".repeat(level), name)?;

	if let Some(message) = &req.message {
		let message = format!("Note: {}", message);
		writeln!(&mut w, "{}", blockquote(&textwrap::fill(&message, 78)))?;
	}

	if req.save.len() > 0 {
		for block in req.save.clone() {
			write!(&mut w, "{}", describe_save(&block)?)?;
		}
	}

	let active_children = collect_active_requirements(&req);

	if let Some(result) = &req.result {
		if let Ok(what_to_do) = summarize_result(&result) {
			let kind = match req.requirements.len() {
				0 => "requirement",
				_ => "section",
			};

			writeln!(
				&mut w,
				"{}\n",
				textwrap::fill(
					&format!(
						"For this {kind}, you must {what_to_do}",
						kind = kind,
						what_to_do = what_to_do
					),
					80,
				)
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

fn describe_save(save: &SaveBlock) -> Result<String, fmt::Error> {
	let mut w = String::new();

	use degreepath_parser::rules::given::Given;

	match save.given {
		Given::AllCourses => match &save.filter.clone() {
			Some(filter) => {
				let filter_desc = describe_courses_filter(&filter);

				let description = format!(
                        "Given the intersection between the following applicable courses and your transcript, but limiting it to only courses taken {}, as “{}”:",
                        filter_desc,
                        save.name,
                    );

				writeln!(&mut w, "{}\n", textwrap::fill(&description, 80),)?;

				writeln!(&mut w, "| Potential | \"{}\" |\n", save.name)?;

				writeln!(&mut w, "- (lists courses that match {:?}\n", save.filter)?;
			}
			None => {
				writeln!(&mut w, "Given the courses from your transcript, TODO")?;
			}
		},
		_ => writeln!(&mut w, "some other save type")?,
	}

	Ok(w)
}

fn summarize_result(rule: &Rule) -> Result<String, fmt::Error> {
	let mut w = String::new();

	match rule {
		Rule::CountOf(rules::count_of::Rule { of, count }) => {
			let all_are_requirements = of.iter().all(|rule| match rule {
				Rule::Requirement { .. } => true,
				_ => false,
			});

			if all_are_requirements && *count == rules::count_of::Counter::All {
				let requirement_names: Vec<String> = of
					.iter()
					.map(|r| print_rule_as_title(&r.clone()).unwrap_or("error!!!".to_string()))
					.collect();

				let names = oxford(requirement_names.as_slice());

				match requirement_names.len() {
					0 => write!(&mut w, "… do nothing")?,
					1 => write!(&mut w, "complete the {} requirement", names)?,
					2 => write!(&mut w, "complete both the {} requirements", names)?,
					_ => write!(&mut w, "complete all of the {} requirements", names)?,
				};
			} else {
				let n = match count {
					rules::count_of::Counter::Any | rules::count_of::Counter::Number(1) => "one".to_string(),
					rules::count_of::Counter::All => "all".to_string(),
					rules::count_of::Counter::Number(n) => format!("{}", n),
				};

				write!(&mut w, "complete {} of the following choices:\n", n)?;

				for req in of {
					write!(&mut w, "\n- {}", summarize_result(&req.clone())?)?;
				}
			}
		}
		Rule::Course(rules::course::Rule { course, .. }) => {
			write!(&mut w, "{}", course.to_string())?;
		}
		Rule::Either(rules::either::Rule { either: pair }) | Rule::Both(rules::both::Rule { both: pair }) => {
			let pair = pair.clone();

			let a = summarize_result(&pair.0)?;
			let b = summarize_result(&pair.1)?;

			match rule {
				Rule::Either(_) => write!(&mut w, "{} or {}", a, b)?,
				Rule::Both(_) => write!(&mut w, "{} and {}", a, b)?,
				_ => panic!("impossible"),
			};
		}
		Rule::Given(given::Rule {
			given,
			action,
			what,
			filter,
			..
		}) => {
			match given {
				given::Given::AreasOfStudy => match what {
					given::What::AreasOfStudy => match action {
						action::Action {
							lhs: action::Value::Command(action::Command::Count),
							op: Some(action::Operator::GreaterThanEqualTo),
							rhs: Some(rhs),
						} => {
							let filter_desc = match filter {
								Some(f) => describe_areas_filter(f),
								None => "".into(),
							};

							let count = match rhs {
								action::Value::Integer(1) => "one",
								action::Value::Integer(2) => "two",
								action::Value::Integer(3) => "three",
								_ => panic!("unknown number"),
							};

							// For this requirement, you must also complete one "major".
							write!(&mut w, "also complete {} {}", count, filter_desc)?;
						}
						_ => panic!("unimplemented"),
					},
					_ => panic!("given: areas, what: !areas???"),
				},
				given::Given::AllCourses => match what {
					given::What::Credits => match action {
						action::Action {
							lhs: action::Value::Command(action::Command::Sum),
							op: Some(action::Operator::GreaterThanEqualTo),
							rhs: Some(rhs),
						} => {
							let filter_desc = match filter {
								Some(f) => describe_courses_filter(f),
								None => "".into(),
							};

							write!(
								&mut w,
								"complete enough courses{} to obtain {} credits",
								filter_desc, rhs
							)?;
						}
						_ => {
							write!(&mut w, "given blah (given: {:?}, action: {:?}", given, action)?;
						}
					},
					given::What::DistinctCourses => match action {
						action::Action {
							lhs: action::Value::Command(action::Command::Count),
							op,
							rhs: Some(rhs),
						} => {
							let filter_desc = match filter {
								Some(f) => describe_courses_filter(f),
								None => "".into(),
							};

							let counter = match op {
								Some(action::Operator::GreaterThanEqualTo) => "at least",
								_ => {
									panic!("other actions for {given: courses, what: courses} are not implemented yet")
								}
							};

							let course_word = match rhs {
								action::Value::Integer(n) if *n == 1 => "course",
								action::Value::Float(n) if *n == 1.0 => "course",
								_ => "courses",
							};

							write!(
								&mut w,
								"complete {counter} {num} distinct {word}{desc}",
								counter = counter,
								num = rhs,
								word = course_word,
								desc = filter_desc
							)?;
						}
						_ => {
							write!(&mut w, "given blah (given: {:?}, action: {:?}", given, action)?;
						}
					},
					given::What::Courses => match action {
						action::Action {
							lhs: action::Value::Command(action::Command::Count),
							op,
							rhs: Some(rhs),
						} => {
							let filter_desc = match filter {
								Some(f) => describe_courses_filter(f),
								None => "".into(),
							};

							let counter = match op {
								Some(action::Operator::GreaterThanEqualTo) => "at least",
								_ => {
									panic!("other actions for {given: courses, what: courses} are not implemented yet")
								}
							};

							let course_word = match rhs {
								action::Value::Integer(n) if *n == 1 => "course",
								action::Value::Float(n) if *n == 1.0 => "course",
								_ => "courses",
							};

							write!(
								&mut w,
								"complete {counter} {num} {word}{desc}",
								counter = counter,
								num = rhs,
								word = course_word,
								desc = filter_desc
							)?;
						}
						_ => {
							write!(&mut w, "given blah (given: {:?}, action: {:?}", given, action)?;
						}
					},
					given::What::Grades => match action {
						action::Action {
							lhs: action::Value::Command(action::Command::Average),
							op: Some(op),
							rhs: Some(rhs),
						} => match op {
							action::Operator::GreaterThanEqualTo => {
								write!(&mut w, "maintain a {} or greater GPA across all of your courses", rhs)?;
							}
							action::Operator::GreaterThan => {
								write!(&mut w, "maintain a GPA above {} across all of your courses", rhs)?;
							}
							action::Operator::EqualTo => {
								write!(&mut w, "maintain exactly a {} GPA across all of your courses", rhs)?;
							}
							action::Operator::NotEqualTo => {
								panic!("not equal to makes no sense here");
							}
							action::Operator::LessThan => {
								write!(&mut w, "maintain less than a {} GPA across all of your courses", rhs)?;
							}
							action::Operator::LessThanEqualTo => {
								write!(&mut w, "maintain at most a {} GPA across all of your courses", rhs)?;
							}
						},
						_ => {
							write!(&mut w, "given blah (given: {:?}, action: {:?}", given, action)?;
						}
					},
					_ => {
						write!(&mut w, "given blah (given: {:?}, action: {:?}", given, action)?;
					}
				},
				_ => {
					write!(&mut w, "given blah (given: {:?}, action: {:?}", given, action)?;
				}
			}
		}
		Rule::Do(rules::action::Rule { .. }) => {
			write!(&mut w, "do blah {:?}", rule)?;
		}
		Rule::Requirement(rules::requirement::Rule { requirement, .. }) => {
			write!(&mut w, "requirement {} blah", requirement)?;
		}
	};

	Ok(w)
}

fn oxford(v: &[String]) -> String {
	match v.len() {
		0 => "".to_string(),
		1 => v[0].to_string(),
		2 => v.join(" and "),
		_ => match v.split_last() {
			Some((last, others)) => format!("{}, and {}", others.join(", "), last),
			_ => panic!("v's len() was > 2, but there weren't two items in it"),
		},
	}
}

fn describe_courses_filter(filter: &filter::Clause) -> String {
	if filter.keys().len() == 2 {
		match (filter.get("semester"), filter.get("year")) {
			(
				Some(filter::WrappedValue::Single(filter::TaggedValue {
					op: action::Operator::EqualTo,
					value: sem,
				})),
				Some(filter::WrappedValue::Single(filter::TaggedValue {
					op: action::Operator::EqualTo,
					value: year,
				})),
			) => return format!(" in the {} of {}", sem, year),
			_ => (),
		};
	}

	let clauses: Vec<String> = filter
		.iter()
		.map(|(k, v)| match v {
			filter::WrappedValue::Single(filter::TaggedValue {
				op: action::Operator::EqualTo,
				value,
			}) => match k.as_ref() {
				"institution" => format!(" at {}", value),
				"level" => format!(" at the {} level", value),
				"gereqs" => format!(" with the {} general education attribute", value),
				"semester" => format!(" in the {} semester", value),
				"year" => format!(" in {}", value),
				// TODO: make Term format better; probably parse into year/term combo
				"term" => format!(" in {}", value),
				"graded" => {
					if v.is_true() {
						", graded,".into()
					} else {
						", non-graded,".into()
					}
				}
				_ => format!(" blargh filter key={}", k),
			},
			filter::WrappedValue::Single(filter::TaggedValue {
				op: action::Operator::GreaterThanEqualTo,
				value,
			}) => match k.as_ref() {
				"level" => format!(" at or above the {} level", value),
				_ => format!(" blargh filter key={}", k),
			},
			_ => format!(" blargh other filter value type"),
		})
		.collect();

	oxford(clauses.as_slice())
}

fn describe_areas_filter(filter: &filter::Clause) -> String {
	let clauses: Vec<String> = filter
		.iter()
		.map(|(k, v)| match v {
			filter::WrappedValue::Single(filter::TaggedValue {
				op: action::Operator::EqualTo,
				value,
			}) => match k.as_ref() {
				"type" => format!("{}", value),
				_ => format!(" blargh filter key={}", k),
			},
			_ => format!(" blargh other filter value type"),
		})
		.collect();

	oxford(clauses.as_slice())
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
			match (*pair.0, *pair.1) {
				(Requirement(r0), Requirement(r1)) => vec![r0, r1],
				(_, Requirement(r1)) => vec![r1],
				(Requirement(r0), _) => vec![r0],
				_ => vec![],
			}
		}
		Given(rule) => match &rule.given {
			given::Given::TheseRequirements { requirements } => requirements.clone(),
			_ => vec![],
		},
		Do(_) => vec![],
	}
}

#[cfg(test)]
mod tests {
	// use super::*;

	// #[test]
	// fn print_top_level() {
	//     let input = AreaOfStudy {
	//
	//     }
	// }
}
