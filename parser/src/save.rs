use crate::rules::given::{action, filter, limit, Given, What};

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct SaveBlock {
	pub name: String,
	#[serde(flatten)]
	pub given: Given,
	#[serde(default)]
	pub limit: Option<Vec<limit::Limiter>>,
	#[serde(rename = "where", default, deserialize_with = "filter::deserialize_with")]
	pub filter: Option<filter::Clause>,
	#[serde(default)]
	pub what: Option<What>,
	#[serde(rename = "do", default, deserialize_with = "action::option_action")]
	pub action: Option<action::Action>,
}

impl crate::rules::traits::PrettyPrint for SaveBlock {
	fn print(&self) -> Result<String, std::fmt::Error> {
		use std::fmt::Write;

		let mut output = String::new();

		match &self.given {
			Given::AllCourses => match &self.filter {
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
			Given::TheseCourses {
				courses,
				repeats: _mode,
			} => {
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
			Given::TheseRequirements { .. } => unimplemented!(),
			Given::AreasOfStudy => unimplemented!(),
			Given::NamedVariable { save } => match &self.filter {
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

		if let Some(_) = &self.limit {
			writeln!(&mut output, "\ntodo: there's a limiter")?;
		}

		Ok(output)
	}
}

#[cfg(test)]
mod tests {
	use super::*;
	use crate::rules::{course, given};

	#[test]
	fn deserialize() {
		let data = r#"---
given: courses
where: { semester: Interim }
what: courses
name: Interim Courses"#;

		let filter: filter::Clause = hashmap! {
			"semester".into() => "Interim".parse::<filter::WrappedValue>().unwrap(),
		};

		let expected = SaveBlock {
			name: "Interim Courses".to_string(),
			given: Given::AllCourses,
			limit: None,
			filter: Some(filter),
			what: Some(What::Courses),
			action: None,
		};

		let actual: SaveBlock = serde_yaml::from_str(&data).unwrap();

		assert_eq!(actual, expected);
	}

	#[test]
	fn deserialize_dance() {
		let data = r#"---
given: these courses
courses: [DANCE 399]
repeats: last
where: {year: graduation-year, semester: Fall}
name: "Senior Dance Seminars""#;

		let filter: filter::Clause = hashmap! {
			"year".into() => "graduation-year".parse::<filter::WrappedValue>().unwrap(),
			"semester".into() => "Fall".parse::<filter::WrappedValue>().unwrap(),
		};

		let expected = SaveBlock {
			name: "Senior Dance Seminars".to_string(),
			given: Given::TheseCourses {
				courses: vec![given::CourseRule::Value(course::Rule {
					course: "DANCE 399".to_string(),
					..Default::default()
				})],
				repeats: given::RepeatMode::Last,
			},
			limit: None,
			filter: Some(filter),
			what: None,
			action: None,
		};

		let actual: SaveBlock = serde_yaml::from_str(&data).unwrap();

		assert_eq!(actual, expected);
	}

	#[test]
	fn pretty_print() {
		use crate::rules::traits::PrettyPrint;

		let input: SaveBlock =
			serde_yaml::from_str(&"{name: Interim, given: courses, where: {semester: Interim}}").unwrap();
		let expected = "Given the subset of courses from your transcript, limited to only courses taken during Interim semesters, as “Interim”:

| “Interim” |
| --------- |
| (todo: list matching courses here) |
";
		assert_eq!(expected, input.print().unwrap());

		let input: SaveBlock = serde_yaml::from_str(&"{name: Interim, given: courses}").unwrap();
		let expected = "Given the courses from your transcript as “Interim”:

| “Interim” |
| --------- |
| (todo: list all??? courses here???) |
";
		assert_eq!(expected, input.print().unwrap());

		let input: SaveBlock =
			serde_yaml::from_str(&"{name: Interim, given: these courses, courses: [THEAT 244], repeats: all}").unwrap();
		let expected =
			"Given the intersection between this set of courses and the courses from your transcript, as “Interim”:

| “Interim” | Transcript |
| --------- | ---------- |
| THEAT 244 | (todo: fill out if match) |
";
		assert_eq!(expected, input.print().unwrap());

		let input: SaveBlock = serde_yaml::from_str(&"{name: Interim, given: save, save: Before}").unwrap();
		let expected = "Given the subset named “Before”, as “Interim”:

| “Interim” |
| --------- |
| (todo: list all??? courses here???) |
";
		assert_eq!(expected, input.print().unwrap());

		let input: SaveBlock =
			serde_yaml::from_str(&"{name: Interim, given: save, save: Before, where: {semester: Interim}}").unwrap();
		let expected = "Given the subset named “Before”, limited it to only courses taken during Interim semesters, as “Interim”:

| “Interim” |
| --------- |
| (todo: list matching courses here) |
";
		assert_eq!(expected, input.print().unwrap());
	}
}
