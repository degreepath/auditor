use super::SaveBlock;
use crate::rules::given::GivenForSaveBlock as Given;
use crate::traits::print;

impl print::Print for SaveBlock {
	fn print(&self) -> print::Result {
		use std::fmt::Write;

		let mut output = String::new();

		match &self.given {
			Given::AllCourses { .. } => match &self.filter {
				Some(f) => {
					write!(&mut output, "Given the subset of courses from your transcript, limited to only courses taken {}, as “{}”:\n\n", f.print()?, self.name)?;

					writeln!(&mut output, "| “{}” |", self.name)?;
					writeln!(&mut output, "| {} |", "-".repeat(self.name.chars().count() + 2))?;
					writeln!(&mut output, "| (todo: list matching courses here) |")?;
				}
				None => {
					write!(
						&mut output,
						"Given the courses from your transcript as “{}”:\n\n",
						self.name
					)?;
					writeln!(&mut output, "| “{}” |", self.name)?;
					writeln!(&mut output, "| {} |", "-".repeat(self.name.chars().count() + 2))?;
					writeln!(&mut output, "| (todo: list all??? courses here???) |")?;
				}
			},
			Given::TheseCourses { courses, .. } => {
				write!(&mut output, "Given the intersection between this set of courses and the courses from your transcript, as “{}”:\n\n", self.name)?;

				let courses = courses.iter().map(|r| r.print().unwrap()).collect::<Vec<String>>();

				let transcript = "Transcript";
				let name_width = self.name.chars().count();

				writeln!(&mut output, "| “{}” | {} |", self.name, transcript)?;
				writeln!(
					&mut output,
					"| {} | {} |",
					"-".repeat(name_width + 2),
					"-".repeat(transcript.len()),
				)?;
				for c in courses {
					writeln!(&mut output, "| {} | (todo: fill out if match) |", c)?;
				}
			}
			Given::TheseRequirements { requirements, .. } => {
				use crate::util::Oxford;

				let req_names = requirements
					.iter()
					.map(|r| format!("“{}”", r))
					.collect::<Vec<String>>()
					.oxford("and");

				write!(
					&mut output,
					"Given the courses which fulfilled the {} requirements",
					req_names
				)?;

				if let Some(filter) = &self.filter {
					write!(&mut output, ", limited to only courses taken {}", filter.print()?)?;
				};

				writeln!(&mut output, ", as “{}”:", self.name)?;

				writeln!(&mut output)?;

				writeln!(&mut output, "| “{}” |", self.name)?;
				writeln!(&mut output, "| {} |", "-".repeat(self.name.chars().count() + 2))?;
				// todo: list matched courses from the referenced save here
				writeln!(&mut output, "| (todo: list matched courses here) |")?;

				writeln!(&mut output)?;

				if let Some(_action) = &self.action {
					// todo: describe what the save's action is doing
					writeln!(&mut output, "> todo: describe what the save's action is doing")?;
				}

				if self.limit.is_some() {
					// todo: describe what the save's limiters do
					writeln!(&mut output, "> todo: describe what the save's limiters do")?;
				}

				// todo: describe what the save will generate
				writeln!(&mut output, "> todo: describe what the save will generate")?;
			}
			Given::NamedVariable { save, .. } => match &self.filter {
				Some(f) => {
					write!(
						&mut output,
						"Given the subset named “{}”, limited it to only courses taken {}, as “{}”:\n\n",
						save,
						f.print()?,
						self.name
					)?;

					writeln!(&mut output, "| “{}” |", self.name)?;
					writeln!(&mut output, "| {} |", "-".repeat(self.name.chars().count() + 2))?;
					writeln!(&mut output, "| (todo: list matching courses here) |")?;
				}
				None => {
					write!(
						&mut output,
						"Given the subset named “{}”, as “{}”:\n\n",
						save, self.name
					)?;
					writeln!(&mut output, "| “{}” |", self.name)?;
					writeln!(&mut output, "| {} |", "-".repeat(self.name.chars().count() + 2))?;
					writeln!(&mut output, "| (todo: list all??? courses here???) |")?;
				}
			},
		}

		// TODO: add a special case for do-block-having SaveBlocks, to show the computed value
		// TODO: decide on something to do for given:these-courses, repeats:all/first/last
		// TODO: add limiter output

		if self.limit.is_some() {
			writeln!(&mut output, "\ntodo: there's a limiter")?;
		}

		Ok(output)
	}
}
