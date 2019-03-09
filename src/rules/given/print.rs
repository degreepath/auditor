use super::{
	CountOnlyAction, CourseRule, GivenAreasWhatOptions, GivenAttendancesWhatOptions, GivenCoursesWhatOptions,
	GivenPerformancesWhatOptions, RepeatMode, Rule,
};
use crate::filter::{AreaClause, AttendanceClause, CourseClause, PerformanceClause};
use crate::limit::Limiter;
use crate::traits::print::{self, Print};
use crate::util::Oxford;
use crate::util::Pluralizable;
use crate::value::{TaggedValue, WrappedValue};

impl print::Print for Rule {
	fn print(&self) -> print::Result {
		use std::fmt::Write;

		let mut output = String::new();

		let rule = match &self {
			Rule::AllCourses { what, filter, limit } => self.print_given_all_courses(what, filter, limit)?,
			Rule::TheseCourses {
				what,
				courses,
				repeats: mode,
				filter,
				limit,
			} => self.print_given_these_courses(courses, mode, what, filter, limit)?,
			Rule::TheseRequirements {
				what,
				requirements,
				filter,
				limit,
			} => self.print_given_these_requirements(requirements, what, filter, limit)?,
			Rule::NamedVariable {
				save,
				what,
				filter,
				limit,
			} => self.print_given_save(save, what, filter, limit)?,
			Rule::Areas { what, filter } => self.print_given_areas(what, filter)?,
			Rule::Performances { what, filter } => self.print_given_performances(what, filter)?,
			Rule::Attendances { what, filter } => self.print_given_attendances(what, filter)?,
		};

		write!(&mut output, "{}", rule)?;

		Ok(output)
	}
}

impl Rule {
	fn print_limits_as_block(&self, limits: &Option<Vec<Limiter>>) -> String {
		match &limits {
			Some(limits) => {
				let stringified: Vec<_> = limits
					.iter()
					.map(|l| {
						let s = if l.at_most == 1 { "" } else { "s" };
						format!(
							"- At most {} course{} may be taken {}",
							l.at_most,
							s,
							l.filter.print().unwrap()
						)
					})
					.collect();

				format!(
					"These courses must fit within the following restrictions:\n\n{}",
					stringified.join("\n")
				)
			}
			None => "".to_string(),
		}
	}

	fn print_limits(&self, limits: &Option<Vec<Limiter>>) -> String {
		match &limits {
			Some(limits) => {
				let stringified: Vec<_> = limits
					.iter()
					.map(|l| {
						let s = if l.at_most == 1 { "" } else { "s" };
						format!(
							"- At most {} course{} may be taken {}",
							l.at_most,
							s,
							l.filter.print().unwrap()
						)
					})
					.collect();

				format!(", subject to the following restrictions:\n\n{}", stringified.join("\n"))
			}
			None => "".to_string(),
		}
	}

	fn print_given_all_courses(
		&self,
		what: &GivenCoursesWhatOptions,
		filter: &Option<CourseClause>,
		limit: &Option<Vec<Limiter>>,
	) -> print::Result {
		use std::fmt::Write;
		use GivenCoursesWhatOptions as What;

		let mut output = String::new();
		let limits = self.print_limits(limit);
		let filter = match &filter {
			Some(f) => format!(" {}", f.print()?),
			None => "".to_string(),
		};

		match &what {
			What::Courses { action: Some(action) } => {
				let plur = action.should_pluralize();
				let action = action.print()?;
				let word = if plur { "courses" } else { "course" };

				write!(&mut output, "take {} {}{}{}", action, word, filter, limits)?;
			}
			What::Courses { action: None } => unimplemented!("what:courses, action:None"),
			What::DistinctCourses { action: Some(action) } => {
				let plur = action.should_pluralize();
				let action = action.print()?;
				let word = if plur { "distinct courses" } else { "course" };

				write!(&mut output, "take {} {}{}{}", action, word, filter, limits)?;
			}
			What::DistinctCourses { action: None } => unimplemented!("what:DistinctCourses, action:None"),
			What::Credits { action: Some(action) } => {
				let plur = action.should_pluralize();
				let action = action.print()?;
				let word = if plur { "credits" } else { "credit" };
				let filter = if filter.is_empty() {
					"".to_owned()
				} else {
					format!(" taken{}", filter)
				};

				write!(
					&mut output,
					"have enough courses{} to obtain {} {}{}",
					filter, action, word, limits
				)?;
			}
			What::Credits { action: None } => unimplemented!("what:Credits, action:None"),
			What::Subjects { action: Some(action) } => {
				let plur = action.should_pluralize();
				let action = action.print()?;
				let word = if plur { "departments" } else { "department" };
				let filter = if filter.is_empty() {
					"".to_owned()
				} else {
					format!(" taken{}", filter)
				};

				write!(
					&mut output,
					"have enough courses{} to span {} {}{}",
					filter, action, word, limits
				)?;
			}
			What::Subjects { action: None } => unimplemented!("what:Subjects, action:None"),
			What::Grades { action: Some(action) } => {
				let plur = action.should_pluralize();
				let action = action.print()?;
				let word = if plur { "courses" } else { "course" };
				let filter = if filter.is_empty() {
					"".to_owned()
				} else {
					format!(" taken{}", filter)
				};

				write!(
					&mut output,
					"maintain an average GPA {} from {}{}{}",
					action, word, filter, limits
				)?;
			}
			What::Grades { action: None } => unimplemented!("what:Grades, action:None"),
			What::Terms { action: Some(action) } => {
				let plur = action.should_pluralize();
				let action = action.print()?;
				let word = if plur { "terms" } else { "term" };

				write!(
					&mut output,
					"have taken enough courses{} to span {} {}{}",
					filter, action, word, limits
				)?;
			}
			What::Terms { action: None } => unimplemented!("what:Terms, action:None"),
		}

		Ok(output)
	}

	fn print_given_areas(&self, what: &GivenAreasWhatOptions, filter: &Option<AreaClause>) -> print::Result {
		use std::fmt::Write;
		use GivenAreasWhatOptions as What;

		let mut output = String::new();
		let filter = match &filter {
			Some(f) => format!(" {}", f.print()?),
			None => "".to_string(),
		};

		match &what {
			What::Areas { action: Some(action) } => {
				// TODO: find a better way to special-case "exactly one" major
				let action = action.print()?;
				let action = action.replace("exactly ", "");
				write!(&mut output, "declare {}{}", action, filter)?;
			}
			What::Areas { action: None } => unimplemented!("what:Areas, action:None"),
		}

		Ok(output)
	}

	fn print_given_performances(
		&self,
		what: &GivenPerformancesWhatOptions,
		filter: &Option<PerformanceClause>,
	) -> print::Result {
		use std::fmt::Write;
		use GivenPerformancesWhatOptions as What;

		let mut output = String::new();
		let filter = match &filter {
			Some(f) => format!(" {}", f.print()?),
			None => "".to_string(),
		};

		match &what {
			What::Performances { action: Some(action) } => {
				let action = action.print()?;
				write!(&mut output, "perform {} recitals{}", action, filter)?;
			}
			What::Performances { action: None } => unimplemented!("what:Performances, action:None"),
		}

		Ok(output)
	}

	fn print_given_attendances(
		&self,
		what: &GivenAttendancesWhatOptions,
		filter: &Option<AttendanceClause>,
	) -> print::Result {
		use std::fmt::Write;
		use GivenAttendancesWhatOptions as What;

		let mut output = String::new();
		let filter = match &filter {
			Some(f) => format!(" {}", f.print()?),
			None => "".to_string(),
		};

		match &what {
			What::Attendances { action: Some(action) } => {
				let action = action.print()?;
				write!(&mut output, "attend {}{} recitals", action, filter)?;
			}
			What::Attendances { action: None } => unimplemented!("what:Attendances, action:None"),
		}

		Ok(output)
	}

	fn print_given_these_courses(
		&self,
		courses: &[CourseRule],
		mode: &RepeatMode,
		what: &GivenCoursesWhatOptions,
		filter: &Option<CourseClause>,
		limit: &Option<Vec<Limiter>>,
	) -> print::Result {
		use std::fmt::Write;
		use GivenCoursesWhatOptions as What;

		let mut output = String::new();
		let limits = self.print_limits(&limit);
		let filter = match &filter {
			Some(f) => Some(format!(" {}", f.print()?)),
			None => None,
		};

		let courses: Vec<String> = courses.iter().map(|r| r.print().unwrap()).collect();

		match (mode, what) {
			(RepeatMode::First, What::Courses { action: Some(action) })
			| (RepeatMode::Last, What::Courses { action: Some(action) }) => {
				match courses.len() {
					1 => {
						// TODO: expose last vs. first in output somehow?
						write!(&mut output, "take {}{}", courses.oxford("and"), limits)?;
					}
					2 => match &action {
						CountOnlyAction::Count(WrappedValue::Single(TaggedValue::GreaterThanEqualTo(n))) => match n {
							1 => {
								write!(&mut output, "take either {} or {}{}", courses[0], courses[1], limits)?;
							}
							2 => {
								write!(&mut output, "take both {} and {}{}", courses[0], courses[1], limits)?;
							}
							_ => panic!("should not require <1 or >len of the number of courses given"),
						},
						_ => unimplemented!("most actions on two-up given:these-courses rules"),
					},
					3...5 => {
						// TODO: expose last vs. first in output somehow?
						let plur = action.should_pluralize();
						let word = if plur { "courses" } else { "course" };
						write!(
							&mut output,
							"take {} {} from among {}{}",
							action.print()?,
							word,
							courses.oxford("and"),
							limits
						)?;
					}
					_ => {
						// TODO: expose last vs. first in output somehow?
						let plur = action.should_pluralize();
						let word = if plur { "courses" } else { "course" };

						let as_list: Vec<_> = courses.iter().map(|l| format!("- {}", l)).collect();

						write!(
							&mut output,
							"take {} {} from among the following:\n\n{}",
							action.print()?,
							word,
							as_list.join("\n")
						)?;

						if !limits.is_empty() {
							write!(&mut output, "\n\n{}", self.print_limits_as_block(&limit))?;
						}
					}
				}
			}
			(RepeatMode::First, What::Courses { action: None }) => {
				unimplemented!("repeats:First, what:Courses, action:None")
			}
			(RepeatMode::Last, What::Courses { action: None }) => {
				unimplemented!("repeats:First, what:Courses, action:None")
			}
			(RepeatMode::All, What::Courses { action: Some(action) }) => {
				// TODO: special-case "once" and "twice"
				let plur = action.should_pluralize();
				let word = if plur { "times" } else { "time" };

				match &action {
					CountOnlyAction::Count(WrappedValue::Single(TaggedValue::GreaterThanEqualTo(1))) => {
						match courses.len() {
							1...5 => {
								write!(
									&mut output,
									"take {} {} {}{}",
									courses.oxford("or"),
									action.print()?,
									word,
									limits
								)?;
							}
							_ => {
								let as_list: Vec<_> = courses.iter().map(|l| format!("- {}", l)).collect();

								write!(
									&mut output,
									"take {} of the following courses:\n\n{}",
									action.print()?,
									as_list.join("\n"),
								)?;

								if !limits.is_empty() {
									write!(&mut output, "\n\n{}", self.print_limits_as_block(&limit))?;
								}
							}
						}
					}
					_ => match courses.len() {
						1 => {
							write!(
								&mut output,
								"take {} {} {}{}",
								courses.oxford("and"),
								action.print()?,
								word,
								limits
							)?;
						}
						_ => {
							write!(
								&mut output,
								"take a combination of {} {} {}{}",
								courses.oxford("and"),
								action.print()?,
								word,
								limits,
							)?;
						}
					},
				}
			}
			(RepeatMode::All, What::Courses { action: None }) => {
				unimplemented!("repeats:All, what:Courses, action:None")
			}
			(RepeatMode::All, What::Credits { action: Some(action) }) => {
				// TODO: special-case "once" and "twice"
				let plur = action.should_pluralize();
				let word = if plur { "credits" } else { "credit" };

				write!(
					&mut output,
					"take {} enough times to yield {} {}{}",
					courses.oxford("and"),
					action.print()?,
					word,
					limits
				)?;
			}
			(RepeatMode::All, What::Credits { action: None }) => {
				unimplemented!("repeats:All, what:Credits, action:None")
			}
			(RepeatMode::All, What::Terms { action: Some(action) }) => {
				// TODO: special-case "once" and "twice"
				let plur = action.should_pluralize();
				let word = if plur { "terms" } else { "term" };

				write!(
					&mut output,
					"take {} enough times to span {} {}{}",
					courses.oxford("and"),
					action.print()?,
					word,
					limits
				)?;
			}
			(RepeatMode::All, What::Terms { action: None }) => unimplemented!("repeats:All, what:Terms, action:None"),
			_ => unimplemented!("certain modes of given:these-courses"),
		}

		if let Some(f) = filter {
			write!(&mut output, "{}", f)?;
		}

		Ok(output)
	}

	fn print_given_these_requirements(
		&self,
		requirements: &[String],
		what: &GivenCoursesWhatOptions,
		filter: &Option<CourseClause>,
		limit: &Option<Vec<Limiter>>,
	) -> print::Result {
		use std::fmt::Write;
		use GivenCoursesWhatOptions as What;

		let mut output = String::new();

		let requirements: Vec<String> = requirements.iter().map(|r| format!("“{}”", r)).collect();

		writeln!(&mut output, "have the following be true:\n")?;
		let mut index = 0;

		index += 1;
		match requirements.len() {
			0 => panic!("no requirements given!"),
			1 | 2 | 3 => {
				let singular = requirements.len() == 1;
				let word = if singular { "requirement" } else { "requirements" };
				writeln!(
					&mut output,
					"{index}. given the results of the {list} {word},",
					index = index,
					list = requirements.oxford("and"),
					word = word
				)?;
			}
			_ => {
				writeln!(
					&mut output,
					"{index}. given the results of the following requirements",
					index = index
				)?;
				for req in requirements {
					writeln!(&mut output, "    - {}", req)?;
				}
			}
		};

		match &filter {
			Some(f) => {
				index += 1;
				writeln!(
					&mut output,
					"{index}. restricted to only courses taken {filter},",
					index = index,
					filter = f.print()?
				)?;
			}
			None => (),
		};

		match &limit {
			Some(_) => {
				index += 1;
				let s = self.print_limits(limit);
				writeln!(
					&mut output,
					"{index}. additionally subject to the following limitations: {s},",
					index = index,
					s = s
				)?;
			}
			None => (),
		};

		index += 1;

		match &what {
			What::Courses { action: Some(action) } => {
				let pluralize = action.should_pluralize();
				let word = if pluralize { "courses" } else { "course" };

				writeln!(
					&mut output,
					"{index}. there must be {action} {word}",
					index = index,
					action = action.print()?,
					word = word,
				)?;
			}
			What::Courses { action: None } => unimplemented!("what:Courses, action:None"),
			What::DistinctCourses { action: Some(action) } => {
				let pluralize = action.should_pluralize();
				let word = if pluralize {
					"distinct courses"
				} else {
					"distinct course"
				};

				writeln!(
					&mut output,
					"{index}. there must be {action} {word}",
					index = index,
					action = action.print()?,
					word = word,
				)?;
			}
			What::DistinctCourses { action: None } => unimplemented!("what:DistinctCourses, action:None"),
			What::Credits { action: Some(action) } => {
				let pluralize = action.should_pluralize();
				let word = if pluralize { "credits" } else { "credit" };

				writeln!(
					&mut output,
					"{index}. there must be {action} {word}",
					index = index,
					action = action.print()?,
					word = word,
				)?;
			}
			What::Credits { action: None } => unimplemented!("what:Credits, action:None"),
			What::Subjects { action: Some(action) } => {
				let pluralize = action.should_pluralize();
				let word = if pluralize {
					"distinct departments"
				} else {
					"department"
				};

				writeln!(
					&mut output,
					"{index}. there must be {action} {word}",
					index = index,
					action = action.print()?,
					word = word,
				)?;
			}
			What::Subjects { action: None } => unimplemented!("what:Subjects, action:None"),
			What::Grades { action: Some(action) } => {
				writeln!(
					&mut output,
					"{index}. there must be an average GPA {action}",
					index = index,
					action = action.print()?,
				)?;
			}
			What::Grades { action: None } => unimplemented!("what:Grades, action:None"),
			What::Terms { action: Some(action) } => {
				let pluralize = action.should_pluralize();
				let word = if pluralize { "terms" } else { "term" };

				writeln!(
					&mut output,
					"{index}. there must be courses in {action} {word}",
					index = index,
					action = action.print()?,
					word = word,
				)?;
			}
			What::Terms { action: None } => unimplemented!("what:Terms, action:None"),
		};

		Ok(output)
	}

	fn print_given_save(
		&self,
		save: &str,
		what: &GivenCoursesWhatOptions,
		filter: &Option<CourseClause>,
		limit: &Option<Vec<Limiter>>,
	) -> print::Result {
		use std::fmt::Write;
		use GivenCoursesWhatOptions as What;

		let mut output = String::new();
		let limits = self.print_limits(limit);
		let filter = match &filter {
			Some(f) => format!(" taken {}", f.print()?),
			None => "".to_string(),
		};

		match &what {
			What::Courses { action: Some(action) } => {
				let plur = action.should_pluralize();
				let word = if plur { "courses" } else { "course" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(
					&mut output,
					"there must be {} {}{}{}",
					action.print()?,
					word,
					filter,
					limits
				)?;
			}
			What::Courses { action: None } => unimplemented!("what:Courses, action:None"),
			What::DistinctCourses { action: Some(action) } => {
				let plur = action.should_pluralize();
				let word = if plur { "distinct courses" } else { "course" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(
					&mut output,
					"there must be {} {}{}{}",
					action.print()?,
					word,
					filter,
					limits
				)?;
			}
			What::DistinctCourses { action: None } => unimplemented!("what:DistinctCourses, action:None"),
			What::Credits { action: Some(action) } => {
				let plur = action.should_pluralize();
				let word = if plur { "credits" } else { "credit" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(
					&mut output,
					"there must be enough courses{} to obtain {} {}{}",
					filter,
					action.print()?,
					word,
					limits
				)?;
			}
			What::Credits { action: None } => unimplemented!("what:Credits, action:None"),
			What::Subjects { action: Some(action) } => {
				let plur = action.should_pluralize();
				let word = if plur { "departments" } else { "department" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(
					&mut output,
					"there must be enough courses{} to span {} {}{}",
					filter,
					action.print()?,
					word,
					limits
				)?;
			}
			What::Subjects { action: None } => unimplemented!("what:Subjects, action:None"),
			What::Grades { action: Some(action) } => {
				let plur = action.should_pluralize();
				let word = if plur { "courses" } else { "course" };

				write!(&mut output, "courses from the subset “{}” ", save)?;
				write!(
					&mut output,
					"must maintain an average GPA {} from {}{}{}",
					action.print()?,
					word,
					filter,
					limits
				)?;
			}
			What::Grades { action: None } => unimplemented!("what:Grades, action:None"),
			What::Terms { action: Some(action) } => {
				let plur = action.should_pluralize();
				let word = if plur { "terms" } else { "term" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(
					&mut output,
					"there must be enough courses{} to span {} {}{}",
					filter,
					action.print()?,
					word,
					limits
				)?;
			}
			What::Terms { action: None } => unimplemented!("what:Terms, action:None"),
		}

		Ok(output)
	}
}
