use super::{AreaClause, AreaType, AttendanceClause, ClassificationYear, CourseClause, PerformanceClause};
use crate::filter::GradeOption;
use crate::grade::Grade;
use crate::student::Semester;
use crate::traits::print;
use crate::traits::print::Print;
use crate::util::Oxford;
use crate::value::{TaggedValue, WrappedValue};

impl print::Print for PerformanceClause {
	fn print(&self) -> print::Result {
		let mut clauses = vec![];

		if let Some(value) = &self.name {
			match value {
				WrappedValue::Single(v) => clauses.push(format!("named “{}”", v.print()?)),
				WrappedValue::Or(_) => clauses.push(format!("named either {}", value.print()?)),
				WrappedValue::And(_) => clauses.push(format!("named both {}", value.print()?)),
			}
		}

		match clauses.len() {
			2 => Ok(clauses.join(", ")),
			_ => Ok(clauses.oxford("and")),
		}
	}
}

impl print::Print for AttendanceClause {
	fn print(&self) -> print::Result {
		let mut clauses = vec![];

		if let Some(value) = &self.name {
			match value {
				WrappedValue::Single(v) => clauses.push(format!("named “{}”", v.print()?)),
				WrappedValue::Or(_) => clauses.push(format!("named either {}", value.print()?)),
				WrappedValue::And(_) => clauses.push(format!("named both {}", value.print()?)),
			}
		}

		match clauses.len() {
			2 => Ok(clauses.join(", ")),
			_ => Ok(clauses.oxford("and")),
		}
	}
}

impl print::Print for AreaClause {
	fn print(&self) -> print::Result {
		use WrappedValue::{And, Or, Single};

		let mut clauses = vec![];

		match (&self.r#type, &self.name) {
			(Some(kind), Some(major)) if *kind == AreaType::Major => match major {
				Single(v) => clauses.push(format!("“{}” major", v.print()?)),
				Or(_) => {
					clauses.push(format!("either a {} major", major.print()?));
				}
				And(_) => unimplemented!("filter:type=major+name, and-value"),
			},
			(Some(kind), None) if *kind == AreaType::Major => match kind {
				Single(_) => clauses.push("major".to_string()),
				Or(_) => {
					clauses.push(format!("either {}", kind.print()?));
				}
				And(_) => unimplemented!("filter:type=major, and-value"),
			},
			(Some(kind), None) => match kind {
				Single(v) => clauses.push(format!("“{}”", v.print()?)),
				Or(_) => {
					clauses.push(format!("either {}", kind.print()?));
				}
				And(_) => unimplemented!("filter:type, and-value"),
			},
			(None, None) => (),
			_ => unimplemented!("certain combinations of type+major keys in a filter"),
		}

		match clauses.len() {
			2 => Ok(clauses.join(", ")),
			_ => Ok(clauses.oxford("and")),
		}
	}
}

impl print::Print for CourseClause {
	fn print(&self) -> print::Result {
		let mut clauses: Vec<String> = vec![];

		if let Some(course) = &self.course {
			clauses.extend(print_course(&course)?);
		}

		if let Some(gereq) = &self.gereqs {
			clauses.extend(print_gereqs(&gereq)?);
		}

		match (&self.year, &self.semester) {
			(Some(year), None) => {
				clauses.extend(print_year(&year)?);
			}
			(None, Some(semester)) => {
				clauses.extend(print_semester(&semester)?);
			}
			(Some(year), Some(semester)) => {
				clauses.extend(print_year_and_semester(&year, &semester)?);
			}
			(None, None) => {}
		}

		if let Some(institution) = &self.institution {
			clauses.extend(print_institution(&institution)?);
		}

		match (&self.subject, &self.number) {
			(Some(subjects), Some(number)) => {
				clauses.push(print_subjects_and_number(&subjects, &number)?);
			}
			(Some(subjects), None) => clauses.push(print_subjects_alone(&subjects)?),
			(None, Some(number)) => {
				clauses.push(print_number_alone(&number)?);
			}
			(None, None) => (),
		};

		if let Some(level) = &self.level {
			clauses.extend(print_level(&level)?);
		}

		if let Some(credits) = &self.credits {
			clauses.extend(print_credits(&credits)?);
		}

		match (&self.graded, &self.grade) {
			(Some(graded), Some(grade)) => clauses.extend(print_grade(Some(&graded), Some(&grade))?),
			(Some(graded), None) => clauses.extend(print_grade(Some(&graded), None)?),
			(None, Some(grade)) => clauses.extend(print_grade(None, Some(&grade))?),
			(None, None) => {}
		}

		if let Some(value) = &self.attribute {
			match value {
				WrappedValue::Single(v) => clauses.push(format!("with the “{}” attribute", v.print()?)),
				WrappedValue::Or(_) => clauses.push(format!("with either the {} attribute", value.print()?)),
				WrappedValue::And(_) => clauses.push(format!("with both the {} attributes", value.print()?)),
			}
		}

		match clauses.len() {
			2 => Ok(clauses.join(", ")),
			_ => Ok(clauses.oxford("and")),
		}
	}
}

fn print_course(value: &WrappedValue<String>) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		WrappedValue::Single(v) => clauses.push(format!("numbered “{}”", v.print()?)),
		WrappedValue::Or(_) | WrappedValue::And(_) => {
			// TODO: figure out how to quote these
			clauses.push(format!("numbered {}", value.print()?));
		}
	};

	Ok(clauses)
}

fn print_gereqs(value: &WrappedValue<String>) -> Result<Vec<String>, std::fmt::Error> {
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

fn print_semester(value: &WrappedValue<Semester>) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		WrappedValue::Single(v) => clauses.push(format!("during {} semesters", v.print()?)),
		WrappedValue::Or(_) | WrappedValue::And(_) => clauses.push(format!("during a {} semester", value.print()?)),
	};

	Ok(clauses)
}

fn print_year(value: &WrappedValue<ClassificationYear>) -> Result<Vec<String>, std::fmt::Error> {
	use {
		TaggedValue::EqualTo,
		WrappedValue::{And, Or, Single},
	};
	let mut clauses = vec![];

	match value {
		Single(EqualTo(y)) => {
			clauses.push(format!("during your {}", y.print()?));
		}
		Or(_) | And(_) => {
			// TODO: implement a .map() function on WrappedValue?
			// to allow something like `year.map(util::expand_year).print()?`
			clauses.push(format!("during your {} **[todo]** years", value.print()?));
		}
		_ => unimplemented!("filter:year, WrappedValue::Single, not using = [0-9] {:?}", value),
	}

	Ok(clauses)
}

fn print_year_and_semester(
	year: &WrappedValue<ClassificationYear>,
	semester: &WrappedValue<Semester>,
) -> Result<Vec<String>, std::fmt::Error> {
	use {TaggedValue::EqualTo, WrappedValue::Single};
	let mut clauses = vec![];

	match (year, semester) {
		(Single(EqualTo(y)), Single(sem)) => {
			clauses.push(format!("during the {} of your {}", sem.print()?, y.print()?))
		}
		_ => unimplemented!("filter:year+semester, certain modes"),
	}

	Ok(clauses)
}

fn print_institution(value: &WrappedValue<String>) -> Result<Vec<String>, std::fmt::Error> {
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

fn print_subjects_alone(subject: &WrappedValue<String>) -> print::Result {
	Ok(match subject {
		WrappedValue::Single(TaggedValue::EqualTo(v)) => format!("within the {} subject code", v),
		WrappedValue::Single(TaggedValue::NotEqualTo(v)) => format!("outside of the {} subject code", v),
		WrappedValue::Single(_) => unimplemented!("filter:subject, only implemented for = and !="),
		WrappedValue::Or(v) => match v.len() {
			2 => format!("within either of the {} subject codes", subject.print()?),
			_ => format!("within the {} subject code", subject.print()?),
		},
		WrappedValue::And(_) => unimplemented!("filter:dept, and-value"),
	})
}

fn print_subjects_and_number(subject: &WrappedValue<String>, number: &WrappedValue<u64>) -> print::Result {
	Ok(match (subject, number) {
		(WrappedValue::Single(TaggedValue::EqualTo(subject)), WrappedValue::Single(TaggedValue::EqualTo(number))) => {
			format!("called {} {} [todo]", subject, number)
		}
		(
			WrappedValue::Single(TaggedValue::EqualTo(subject)),
			WrappedValue::Single(TaggedValue::NotEqualTo(number)),
		) => format!("other than {} {}", subject, number),
		(WrappedValue::Or(v), WrappedValue::Single(TaggedValue::GreaterThanEqualTo(n))) => match v.len() {
			1 => format!("within the {} subject code past {}", subject.print()?, n),
			2 => format!("within either of the {} subject codes, past {}", subject.print()?, n),
			_ => format!("within any of the {} subject codes past {}", subject.print()?, n),
		},
		_ => unimplemented!("filter:dept+num, certain modes"),
	})
}

fn print_number_alone(number: &WrappedValue<u64>) -> print::Result {
	Ok(match number {
		WrappedValue::Single(TaggedValue::EqualTo(v)) => format!("numbered {}", v),
		WrappedValue::Single(TaggedValue::NotEqualTo(v)) => format!("not numbered {}", v),
		_ => unimplemented!("filter:num, certain modes"),
	})
}

fn print_level(value: &WrappedValue<u64>) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		WrappedValue::Single(TaggedValue::GreaterThanEqualTo(v)) => {
			clauses.push(format!("at or above the {} level", v))
		}
		WrappedValue::Single(v) => clauses.push(format!("at the {} level", v.print()?)),
		WrappedValue::Or(_) => {
			clauses.push(format!("at either the {} level", value.print()?));
		}
		WrappedValue::And(_) => unimplemented!("filter:level, and-value"),
	}

	Ok(clauses)
}

fn print_credits(value: &WrappedValue<decorum::R32>) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		WrappedValue::Single(TaggedValue::GreaterThanEqualTo(v)) => {
			clauses.push(format!("worth at least {:>0.2} credits", v))
		}
		WrappedValue::Single(TaggedValue::EqualTo(v)) => clauses.push(format!("worth {:>0.2} credits", v)),
		WrappedValue::Single(_) => unimplemented!("filter:credits, certain modes"),
		WrappedValue::Or(_) => {
			clauses.push(format!("worth either {} credits", value.print()?));
		}
		WrappedValue::And(_) => unimplemented!("filter:credits, and-value"),
	}

	Ok(clauses)
}

fn print_grade(
	value: Option<&WrappedValue<GradeOption>>,
	grade: Option<&WrappedValue<Grade>>,
) -> Result<Vec<String>, std::fmt::Error> {
	let mut clauses = vec![];

	match value {
		Some(value) => match value {
			WrappedValue::Or(_) | WrappedValue::And(_) => {}
			WrappedValue::Single(TaggedValue::EqualTo(value)) => match value {
				GradeOption::Graded => match grade {
					Some(grade) => clauses.push(format!("courses sucessfully completed with at least a {}", grade)),
					None => clauses.push("as _graded_ courses".to_string()),
				},
				GradeOption::Audit => {
					clauses.push("as _audited_ courses".to_string());
				}
				GradeOption::Pn => {
					clauses.push("as courses taken p/n".to_string());
				}
				GradeOption::Su => {
					clauses.push("as courses taken s/u".to_string());
				}
				GradeOption::NoGrade => clauses.push("as _not graded_ courses".to_string()),
			},
			WrappedValue::Single(_) => unimplemented!("printing \"graded\" with anything other than equal-to"),
		},
		None => match grade {
			Some(grade) => clauses.push(format!("courses sucessfully completed with at least a {}", grade)),
			None => {}
		},
	}

	Ok(clauses)
}
