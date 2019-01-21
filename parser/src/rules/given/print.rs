use super::*;
use crate::traits::print;
use crate::traits::print::Print;
use crate::util::Oxford;

impl print::Print for Rule {
	fn print(&self) -> print::Result {
		use std::fmt::Write;

		let mut output = String::new();

		let rule = match &self.given {
			Given::AllCourses => self.print_given_all_courses()?,
			Given::TheseCourses { courses, repeats: mode } => self.print_given_these_courses(courses, mode)?,
			Given::TheseRequirements { requirements } => self.print_given_these_requirements(requirements)?,
			Given::AreasOfStudy => self.print_given_areas()?,
			Given::NamedVariable { save } => self.print_given_save(save)?,
		};

		write!(&mut output, "{}", rule)?;

		Ok(output)
	}
}

impl Rule {
	fn print_filter(&self) -> print::Result {
		match &self.filter {
			Some(f) => Ok(format!(" {}", f.print()?)),
			None => Ok("".to_string()),
		}
	}

	fn print_given_all_courses(&self) -> print::Result {
		use std::fmt::Write;

		let mut output = String::new();
		let filter = self.print_filter()?;

		match &self.what {
			What::Courses => {
				let plur = self.action.should_pluralize();
				let word = if plur { "courses" } else { "course" };

				write!(&mut output, "have {} {}{}", self.action.print()?, word, filter)?;
			}
			What::DistinctCourses => {
				let plur = self.action.should_pluralize();
				let word = if plur { "distinct courses" } else { "course" };

				write!(&mut output, "have {} {}{}", self.action.print()?, word, filter)?;
			}
			What::Credits => {
				let plur = self.action.should_pluralize();
				let word = if plur { "credits" } else { "credit" };

				write!(
					&mut output,
					"have enough courses{} to obtain {} {}",
					filter,
					self.action.print()?,
					word
				)?;
			}
			What::Departments => {
				let plur = self.action.should_pluralize();
				let word = if plur { "departments" } else { "department" };

				write!(
					&mut output,
					"have enough courses{} to span {} {}",
					filter,
					self.action.print()?,
					word
				)?;
			}
			What::Grades => {
				let plur = self.action.should_pluralize();
				let word = if plur { "courses" } else { "course" };

				write!(
					&mut output,
					"maintain an average GPA {} from {}{}",
					self.action.print()?,
					word,
					filter
				)?;
			}
			What::Terms => {
				let plur = self.action.should_pluralize();
				let word = if plur { "terms" } else { "term" };

				write!(
					&mut output,
					"have enough courses{} to span {} {}",
					filter,
					self.action.print()?,
					word
				)?;
			}
			What::AreasOfStudy => panic!("given:all-courses and what:area makes no sense"),
		}

		Ok(output)
	}

	fn print_given_areas(&self) -> print::Result {
		use std::fmt::Write;

		let mut output = String::new();
		let filter = self.print_filter()?;

		match self.what {
			What::AreasOfStudy => {
				// TODO: find a better way to special-case "exactly one" major
				let action = self.action.print()?;
				let action = action.replace("exactly ", "");
				write!(&mut output, "declare {}{}", action, filter)?;
			}
			_ => panic!("given: areas, what: !areas…"),
		}

		Ok(output)
	}

	fn print_given_these_courses(&self, courses: &Vec<super::CourseRule>, mode: &super::RepeatMode) -> print::Result {
		use std::fmt::Write;

		let mut output = String::new();
		// let filter = self.print_filter()?;

		let courses_vec = courses;
		let courses = courses
			.iter()
			.map(|r| r.print().unwrap())
			.collect::<Vec<String>>()
			.oxford("and");

		match (mode, &self.what) {
			(RepeatMode::First, What::Courses) | (RepeatMode::Last, What::Courses) => {
				match courses_vec.len() {
					1 => {
						// TODO: expose last vs. first in output somehow?
						write!(&mut output, "take {}", courses)?;
					}
					2 => match (&self.action.lhs, &self.action.op, &self.action.rhs) {
						(
							action::Value::Command(action::Command::Count),
							Some(action::Operator::GreaterThanEqualTo),
							Some(action::Value::Integer(n)),
						) => match n {
							1 => {
								write!(
									&mut output,
									"take either {} or {}",
									courses_vec[0].print()?,
									courses_vec[1].print()?
								)?;
							}
							2 => {
								write!(
									&mut output,
									"take both {} and {}",
									courses_vec[0].print()?,
									courses_vec[1].print()?
								)?;
							}
							_ => panic!("should not require <1 or >len of the number of courses given"),
						},
						_ => unimplemented!("most actions on two-up given:these-courses rules"),
					},
					_ => {
						// TODO: expose last vs. first in output somehow?
						let plur = self.action.should_pluralize();
						let word = if plur { "courses" } else { "course" };
						write!(
							&mut output,
							"take {} {} from among {}",
							self.action.print()?,
							word,
							courses
						)?;
					}
				}
			}
			(RepeatMode::All, What::Courses) => {
				// TODO: special-case "once" and "twice"
				let plur = self.action.should_pluralize();
				let word = if plur { "times" } else { "time" };

				write!(&mut output, "take {} {} {}", courses, self.action.print()?, word)?;
			}
			(RepeatMode::All, What::Credits) => {
				// TODO: special-case "once" and "twice"
				let plur = self.action.should_pluralize();
				let word = if plur { "credits" } else { "credit" };

				write!(
					&mut output,
					"take {} enough times to yield {} {}",
					courses,
					self.action.print()?,
					word
				)?;
			}
			(RepeatMode::All, What::Terms) => {
				// TODO: special-case "once" and "twice"
				let plur = self.action.should_pluralize();
				let word = if plur { "terms" } else { "term" };

				write!(
					&mut output,
					"take {} enough times to span {} {}",
					courses,
					self.action.print()?,
					word
				)?;
			}
			_ => unimplemented!("certain modes of given:these-courses"),
		}

		Ok(output)
	}

	fn print_given_these_requirements(&self, requirements: &Vec<super::req_ref::Rule>) -> print::Result {
		use std::fmt::Write;

		let mut output = String::new();
		let filter = self.print_filter()?;

		let requirements: Vec<String> = requirements
			.into_iter()
			.filter_map(|r| match r.print() {
				Ok(p) => Some(p),
				Err(_) => None,
			})
			.collect();

		let singular = requirements.len() == 1;
		let reqs_word = if singular { "requirement" } else { "requirements" };
		let ending = format!("matched by the {} {}", requirements.oxford("and"), reqs_word);

		match &self.what {
			What::Courses => {
				let plur = self.action.should_pluralize();
				let word = if plur { "courses" } else { "course" };

				write!(
					&mut output,
					"have {} {}{} in the set of courses {}",
					self.action.print()?,
					word,
					filter,
					ending
				)?;
			}
			What::DistinctCourses => {
				let plur = self.action.should_pluralize();
				let word = if plur { "distinct courses" } else { "distinct course" };

				write!(
					&mut output,
					"have {} {}{} in the set of courses {}",
					self.action.print()?,
					word,
					filter,
					ending
				)?;
			}
			What::Credits => {
				let plur = self.action.should_pluralize();
				let word = if plur { "credits" } else { "credit" };

				write!(
					&mut output,
					"take enough courses{} to obtain {} {} from the set of courses {}",
					filter,
					self.action.print()?,
					word,
					ending
				)?;
			}
			What::Departments => {
				let plur = self.action.should_pluralize();
				let word = if plur { "departments" } else { "department" };

				write!(
					&mut output,
					"take enough courses{} to span {} {} from the set of courses {}",
					filter,
					self.action.print()?,
					word,
					ending
				)?;
			}
			What::Grades => {
				let plur = self.action.should_pluralize();
				let word = if plur { "courses" } else { "course" };

				write!(
					&mut output,
					"maintain an average GPA {} from {}{} from the set of courses {}",
					self.action.print()?,
					word,
					filter,
					ending
				)?;
			}
			What::Terms => {
				let plur = self.action.should_pluralize();
				let word = if plur { "terms" } else { "term" };

				write!(
					&mut output,
					"take enough courses{} to span {} {} from the set of courses {}",
					filter,
					self.action.print()?,
					word,
					ending
				)?;
			}
			What::AreasOfStudy => unimplemented!("given:these-requirements, what:areas makes no sense"),
		};

		Ok(output)
	}

	fn print_given_save(&self, save: &str) -> print::Result {
		use std::fmt::Write;

		let mut output = String::new();
		let filter = self.print_filter()?;

		match &self.what {
			What::Courses => {
				let plur = self.action.should_pluralize();
				let word = if plur { "courses" } else { "course" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(&mut output, "there must be {} {}{}", self.action.print()?, word, filter)?;
				// write!(&mut output, " in the subset “{}”", save)?;
			}
			What::DistinctCourses => {
				let plur = self.action.should_pluralize();
				let word = if plur { "distinct courses" } else { "course" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(&mut output, "there must be {} {}{}", self.action.print()?, word, filter)?;
				// write!(&mut output, " in the subset “{}”", save)?;
			}
			What::Credits => {
				let plur = self.action.should_pluralize();
				let word = if plur { "credits" } else { "credit" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(
					&mut output,
					"there must be enough courses{} to obtain {} {}",
					filter,
					self.action.print()?,
					word
				)?;
			}
			What::Departments => {
				let plur = self.action.should_pluralize();
				let word = if plur { "departments" } else { "department" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(
					&mut output,
					"there must be enough courses{} to span {} {}",
					filter,
					self.action.print()?,
					word
				)?;
			}
			What::Grades => {
				let plur = self.action.should_pluralize();
				let word = if plur { "courses" } else { "course" };

				write!(&mut output, "courses from the subset “{}” ", save)?;
				write!(
					&mut output,
					"must maintain an average GPA {} from {}{}",
					self.action.print()?,
					word,
					filter
				)?;
			}
			What::Terms => {
				let plur = self.action.should_pluralize();
				let word = if plur { "terms" } else { "term" };

				write!(&mut output, "in the subset “{}”, ", save)?;
				write!(
					&mut output,
					"there must be enough courses{} to span {} {}",
					filter,
					self.action.print()?,
					word
				)?;
			}
			What::AreasOfStudy => unimplemented!("given:variable, what:areas is not yet implemented"),
		}

		Ok(output)
	}
}
