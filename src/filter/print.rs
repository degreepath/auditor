use super::constant::Constant;
use super::Clause;
use crate::traits::print;
use crate::traits::print::Print;
use crate::util::{self, Oxford};
use crate::value::{SingleValue, TaggedValue, WrappedValue};
use std::collections::HashSet;

impl print::Print for Clause {
	fn print(&self) -> print::Result {
		let mut clauses = vec![];

		let mut used_keys = HashSet::new();

		if let Some(gereq) = self.get("gereqs") {
			used_keys.insert("gereqs".to_string());
			clauses.extend(print_gereqs(gereq)?);
		}

		match (self.get("year"), self.get("semester")) {
			(Some(year), None) => {
				used_keys.insert("year".to_string());
				clauses.extend(print_year(year)?);
			}
			(None, Some(semester)) => {
				used_keys.insert("semester".to_string());
				clauses.extend(print_semester(semester)?);
			}
			(Some(year), Some(semester)) => {
				used_keys.extend(vec!["semester".to_string(), "year".to_string()]);
				clauses.extend(print_year_and_semester(year, semester)?);
			}
			(None, None) => {}
		}

		if let Some(institution) = self.get("institution") {
			used_keys.insert("institution".to_string());
			clauses.extend(print_institution(institution)?);
		}

		{
			// handle the dept/num/section combo here
			let (dept, num, sect) = (self.get("department"), self.get("number"), self.get("section"));
			let (used, new_clauses) = print_dept_num_section(dept, num, sect)?;
			used_keys.extend(used);
			clauses.extend(new_clauses);
		}

		if let Some(level) = self.get("level") {
			used_keys.insert("level".to_string());
			clauses.extend(print_level(level)?);
		}

		if let Some(graded) = self.get("graded") {
			used_keys.insert("graded".to_string());
			clauses.extend(print_graded(graded)?);
		}

		{
			// handle type/name combinations for major queries here
			let (used, new_clauses) = print_type_name_combo(self.get("type"), self.get("name"))?;
			used_keys.extend(used);
			clauses.extend(new_clauses);
		}

		if let Some(value) = self.get("attribute") {
			used_keys.insert("attribute".to_string());

			match value {
				WrappedValue::Single(v) => clauses.push(format!("with the “{}” attribute", v.print()?)),
				WrappedValue::Or(_) => clauses.push(format!("with either the {} attribute", value.print()?)),
				WrappedValue::And(_) => clauses.push(format!("with both the {} attributes", value.print()?)),
			}
		}

		for key in self.keys() {
			if used_keys.contains(key) {
				continue;
			}

			if let Some(value) = self.get(key) {
				match value {
					WrappedValue::Single(v) => {
						clauses.push(format!("with the “{}” `{}` attribute", v.print()?, key))
					}
					WrappedValue::Or(_) => {
						clauses.push(format!("with either the {} `{}` attribute", value.print()?, key))
					}
					WrappedValue::And(_) => {
						clauses.push(format!("with both the {} `{}` attribute", value.print()?, key));
					}
				}
			}
		}

		match clauses.len() {
			2 => Ok(clauses.join(", ")),
			_ => Ok(clauses.oxford("and")),
		}
	}
}

fn print_gereqs(value: &WrappedValue) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		WrappedValue::Single(v) => clauses.push(format!("with the “{}” general education attribute", v.print()?)),
		WrappedValue::Or(_) | WrappedValue::And(_) => {
			// TODO: figure out how to quote these
			clauses.push(format!("with the {} general education attribute", value.print()?));
		}
	};

	Ok(clauses)
}

fn print_semester(value: &WrappedValue) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		WrappedValue::Single(v) => clauses.push(format!("during {} semesters", v.print()?)),
		WrappedValue::Or(_) | WrappedValue::And(_) => clauses.push(format!("during a {} semester", value.print()?)),
	};

	Ok(clauses)
}

fn print_year(value: &WrappedValue) -> Result<Vec<String>, std::fmt::Error> {
	use {
		TaggedValue::EqualTo,
		WrappedValue::{And, Or, Single},
	};
	let mut clauses = vec![];

	match value {
		Single(EqualTo(SingleValue::Integer(n))) => {
			clauses.push(format!("during the {} academic year", util::expand_year(*n, "dual")))
		}
		Single(EqualTo(SingleValue::String(s))) if *s == Constant::GraduationYear => {
			clauses.push("during your graduation year".to_string())
		}
		Or(_) | And(_) => {
			// TODO: implement a .map() function on WrappedValue?
			// to allow something like `year.map(util::expand_year).print()?`
			clauses.push(format!("during the {} academic years", value.print()?));
		}
		_ => unimplemented!("filter:year, WrappedValue::Single, not using = [0-9] {:?}", value),
	}

	Ok(clauses)
}

fn print_year_and_semester(year: &WrappedValue, semester: &WrappedValue) -> Result<Vec<String>, std::fmt::Error> {
	use {TaggedValue::EqualTo, WrappedValue::Single};
	let mut clauses = vec![];

	match (year, semester) {
		(Single(EqualTo(SingleValue::Integer(year))), Single(sem)) => clauses.push(format!(
			"during the {} of the {} academic year",
			sem.print()?,
			util::expand_year(*year, "dual")
		)),
		(Single(EqualTo(SingleValue::String(s))), Single(sem)) if *s == Constant::GraduationYear => {
			clauses.push(format!("during the {} of your graduation year", sem.print()?))
		}
		_ => unimplemented!("filter:year+semester, certain modes"),
	}

	Ok(clauses)
}

fn print_institution(value: &WrappedValue) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		WrappedValue::Single(v) => clauses.push(format!("at {}", v.print()?)),
		WrappedValue::Or(_) => {
			clauses.push(format!("at either {}", value.print()?));
		}
		WrappedValue::And(_) => unimplemented!("filter:institution, and-value"),
	}

	Ok(clauses)
}

fn print_department_alone(department: &WrappedValue) -> print::Result {
	Ok(match department {
		WrappedValue::Single(TaggedValue::EqualTo(v)) => format!("within the {} department", v.print()?),
		WrappedValue::Single(TaggedValue::NotEqualTo(v)) => format!("outside of the {} department", v.print()?),
		WrappedValue::Single(_) => unimplemented!("filter:department, only implemented for = and !="),
		WrappedValue::Or(v) => match v.len() {
			2 => format!("within either of the {} departments", department.print()?),
			_ => format!("within the {} department", department.print()?),
		},
		WrappedValue::And(_) => unimplemented!("filter:dept, and-value"),
	})
}

fn print_department_and_number(department: &WrappedValue, number: &WrappedValue) -> print::Result {
	Ok(match (department, number) {
		(
			WrappedValue::Single(TaggedValue::EqualTo(department)),
			WrappedValue::Single(TaggedValue::EqualTo(number)),
		) => format!("called {} {} [todo]", department.print()?, number.print()?),
		(
			WrappedValue::Single(TaggedValue::EqualTo(department)),
			WrappedValue::Single(TaggedValue::NotEqualTo(number)),
		) => format!("other than {} {}", department.print()?, number.print()?),
		(WrappedValue::Or(v), WrappedValue::Single(TaggedValue::GreaterThanEqualTo(n))) => match v.len() {
			1 => format!("within the {} department past {}", department.print()?, n.print()?),
			2 => format!(
				"within either of the {} departments, past {}",
				department.print()?,
				n.print()?
			),
			_ => format!(
				"within any of the {} departments past {}",
				department.print()?,
				n.print()?
			),
		},
		_ => unimplemented!("filter:dept+num, certain modes"),
	})
}

fn print_number_alone(number: &WrappedValue) -> print::Result {
	Ok(match number {
		WrappedValue::Single(TaggedValue::EqualTo(v)) => format!("numbered {}", v.print()?),
		WrappedValue::Single(TaggedValue::NotEqualTo(v)) => format!("not numbered {}", v.print()?),
		_ => unimplemented!("filter:num, certain modes"),
	})
}

fn print_dept_num_section(
	department: Option<&WrappedValue>,
	number: Option<&WrappedValue>,
	section: Option<&WrappedValue>,
) -> Result<(HashSet<String>, Vec<String>), std::fmt::Error> {
	let mut clauses = vec![];
	let mut used_keys = HashSet::new();

	match (department, number, section) {
		(Some(department), None, None) => {
			used_keys.insert("department".to_string());
			clauses.push(print_department_alone(department)?)
		}
		(Some(department), Some(number), None) => {
			used_keys.insert("department".to_string());
			used_keys.insert("number".to_string());
			clauses.push(print_department_and_number(department, number)?);
		}
		(None, Some(number), None) => {
			used_keys.insert("number".to_string());
			clauses.push(print_number_alone(number)?);
		}
		(Some(_), Some(_), Some(_)) => unimplemented!("filter:department+section"),
		(Some(_), None, Some(_)) => unimplemented!("filter:department+section"),
		(None, Some(_), Some(_)) => unimplemented!("filter:number+section"),
		(None, None, Some(_)) => unimplemented!("filter:section"),
		(None, None, None) => (),
	};

	Ok((used_keys, clauses))
}

fn print_level(value: &WrappedValue) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		WrappedValue::Single(TaggedValue::GreaterThanEqualTo(v)) => {
			clauses.push(format!("at or above the {} level", v.print()?))
		}
		WrappedValue::Single(v) => clauses.push(format!("at the {} level", v.print()?)),
		WrappedValue::Or(_) => {
			clauses.push(format!("at either the {} level", value.print()?));
		}
		WrappedValue::And(_) => unimplemented!("filter:level, and-value"),
	}

	Ok(clauses)
}

fn print_graded(value: &WrappedValue) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	if *value == true {
		clauses.push("as \"graded\" courses".to_string());
	} else if *value == false {
		clauses.push("as _not_ \"graded\" courses".to_string());
	} else {
		unimplemented!("filter:graded, {:?}", value)
	}

	Ok(clauses)
}

fn print_type_name_combo(
	kind: Option<&WrappedValue>,
	name: Option<&WrappedValue>,
) -> Result<(HashSet<String>, Vec<String>), std::fmt::Error> {
	let mut clauses = vec![];
	let mut used_keys = HashSet::new();

	match (kind, name) {
		(Some(kind), Some(major)) if *kind == WrappedValue::new("major") => {
			used_keys.insert("type".to_string());
			used_keys.insert("name".to_string());

			match major {
				WrappedValue::Single(v) => clauses.push(format!("“{}” major", v.print()?)),
				WrappedValue::Or(_) => {
					clauses.push(format!("either a {} major", major.print()?));
				}
				WrappedValue::And(_) => unimplemented!("filter:type=major+name, and-value"),
			}
		}
		(Some(kind), None) if *kind == WrappedValue::new("major") => {
			used_keys.insert("type".to_string());
			match kind {
				WrappedValue::Single(_) => clauses.push("major".to_string()),
				WrappedValue::Or(_) => {
					clauses.push(format!("either {}", kind.print()?));
				}
				WrappedValue::And(_) => unimplemented!("filter:type=major, and-value"),
			}
		}
		(Some(kind), None) => {
			used_keys.insert("type".to_string());
			match kind {
				WrappedValue::Single(v) => clauses.push(format!("“{}”", v.print()?)),
				WrappedValue::Or(_) => {
					clauses.push(format!("either {}", kind.print()?));
				}
				WrappedValue::And(_) => unimplemented!("filter:type, and-value"),
			}
		}
		(None, None) => (),
		_ => unimplemented!("certain combinations of type+major keys in a filter"),
	}

	Ok((used_keys, clauses))
}
