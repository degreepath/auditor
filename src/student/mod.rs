use crate::audit::Transcript;
use overrides::Override;
use serde::{Deserialize, Serialize};

mod data;
pub use data::{AreaDescriptor, AttendanceInstance, CourseInstance, OrganizationDescriptor, PerformanceInstance};
pub use data::{CourseType, GradeOption, Semester};

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
