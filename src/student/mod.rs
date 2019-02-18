use crate::audit::Transcript;
use crate::filterable_data::FilterableData;
use overrides::Override;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct StudentData {
	pub transcript: Transcript,
	pub organizations: Vec<OrganizationDescriptor>,
	pub performances: Vec<PerformanceInstance>,
	pub attendances: Vec<AttendanceInstance>,
	pub areas: Vec<AreaDescriptor>,
	pub overrides: Vec<Override>,
}

impl StudentData {
	pub fn update_transcript(self, courses: &[CourseInstance]) -> StudentData {
		StudentData {
			transcript: Transcript::new(courses),
			..self
		}
	}
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AreaDescriptor(FilterableData);

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct OrganizationDescriptor(FilterableData);

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct PerformanceInstance(FilterableData);

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AttendanceInstance(FilterableData);

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CourseInstance(FilterableData);

impl CourseInstance {
	pub fn new(data: FilterableData) -> CourseInstance {
		CourseInstance(data)
	}
}

impl std::ops::Deref for CourseInstance {
	type Target = FilterableData;

	fn deref(&self) -> &Self::Target {
		&self.0
	}
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Term {
	pub year: u16,
	pub semester: Semester,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Semester {
	Fall,
	Interim,
	Spring,
	#[serde(rename = "Summer Session 1")]
	Summer1,
	#[serde(rename = "Summer Session 2")]
	Summer2,
	#[serde(rename = "Non-St. Olaf")]
	NonStOlaf,
}

impl std::str::FromStr for Semester {
	type Err = crate::util::ParseError;

	fn from_str(s: &str) -> Result<Self, Self::Err> {
		use crate::util::ParseError;

		match s.trim() {
			"Fall" => Ok(Semester::Fall),
			"Interim" => Ok(Semester::Interim),
			"Spring" => Ok(Semester::Spring),
			"Summer Session 1" => Ok(Semester::Summer1),
			"Summer Session 2" => Ok(Semester::Summer2),
			"Non-St. Olaf" => Ok(Semester::NonStOlaf),
			_ => Err(ParseError::InvalidValue),
		}
	}
}

impl std::fmt::Display for Semester {
	fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
		use Semester::*;

		match &self {
			Fall => write!(f, "Fall"),
			Interim => write!(f, "Interim"),
			Spring => write!(f, "Spring"),
			Summer1 => write!(f, "Summer Session 1"),
			Summer2 => write!(f, "Summer Session 2"),
			NonStOlaf => write!(f, "Non-St. Olaf"),
		}
	}
}

pub mod overrides {
	use super::{AreaDescriptor, AttendanceInstance, CourseInstance, PerformanceInstance};
	use serde::{Deserialize, Serialize};

	#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
	pub struct Override {
		pub path: Vec<PathSegment>,
		#[serde(default)]
		pub value: Option<Value>,
		pub mode: Mode,
	}

	#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
	pub enum Mode {
		Pass,
		AllowValue,
	}

	#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
	pub enum Value {
		Course(CourseInstance),
		Area(AreaDescriptor),
		Performance(PerformanceInstance),
		Attendance(AttendanceInstance),
	}

	#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
	pub enum PathSegment {
		Root,
		Requirement(String),
		Path(String),
		Index(u16),
	}

	mod tests {
		// /, :Core, .result, .of, #4, .either, #0
		// [Root, Requirement("Core"), Path("result"), Path("of"), Index(4), Path("either"), Index(0)]
	}
}
