use crate::traits::print;
use indexmap::IndexMap;
use std::collections::HashSet;

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Attributes {
	#[serde(default)]
	pub multicountable: Vec<Vec<Matchable>>,
	#[serde(default)]
	pub courses: IndexMap<CourseReference, Vec<String>>,
}

type CourseReference = String;

#[derive(Debug, PartialEq, Eq, Hash, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Matchable {
	CourseId { course: String },
	Attribute { attribute: String },
	GeReq { gereq: String },
}

const CHECKMARK: &str = "✅";
const RED_X: &str = "❌";

impl print::Print for Attributes {
	fn print(&self) -> print::Result {
		use std::fmt::Write;
		let mut w = String::new();

		let all_attributes = get_all_unique_values(self.courses.values().cloned());
		let table_size = all_attributes.len() + 1;

		let mut header: Vec<String> = Vec::with_capacity(table_size);
		header.push("Courses".to_string());
		header.extend(all_attributes.iter().map(|n| format!("`{}`", n)).collect::<Vec<_>>());
		writeln!(&mut w, "{}", header.join(" | "))?;

		let divider: Vec<&str> = std::iter::repeat(":---:").take(table_size - 1).collect();
		writeln!(&mut w, "--- | {}", divider.join(" | "))?;

		for (course, attributes) in &self.courses {
			let mut row: Vec<String> = Vec::with_capacity(table_size);

			row.push(course.clone());

			for attr in all_attributes.clone() {
				let mark = if attributes.contains(&attr) { CHECKMARK } else { RED_X };
				row.push(String::from(mark));
			}

			writeln!(&mut w, "{}", row.join(" | "))?;
		}

		Ok(w)
	}
}

fn get_all_unique_values<T>(data: T) -> Vec<String>
where
	T: Iterator<Item = Vec<String>>,
{
	let all_attributes: HashSet<String> = data.flat_map(|c| c.clone()).collect();
	let mut all_attributes: Vec<String> = all_attributes.iter().cloned().collect();
	all_attributes.sort();
	all_attributes
}
