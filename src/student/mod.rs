use crate::audit::{CourseInstance, Transcript};
use serde::{Deserialize, Serialize};

use crate::area_of_study::AreaType;
use attendance::AttendanceInstance;
use organization::OrganizationDescriptor;
use overrides::Override;
use performance::PerformanceInstance;

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct StudentData {
	pub transcript: Transcript,
	pub organizations: Vec<OrganizationDescriptor>,
	pub performances: Vec<PerformanceInstance>,
	pub attendances: Vec<AttendanceInstance>,
	pub areas: Vec<AreaDescriptor>,
	pub overrides: Vec<Override>,
}

#[derive(Debug, Clone, PartialEq, PartialOrd, Ord, Eq, Serialize, Deserialize)]
pub struct AreaDescriptor {
	pub name: String,
	pub catalog: String,
	#[serde(flatten)]
	pub area_type: AreaType,
	pub institution: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct Term {
	pub year: u16,
	pub semester: Semester,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, Hash, Ord, PartialOrd)]
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

mod organization {
	use super::Term;
	use serde::{Deserialize, Serialize};

	#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
	pub struct OrganizationDescriptor {
		pub name: String,
		pub role: String,
		pub term: Term,
	}
}

mod performance {
	use super::Term;
	use serde::{Deserialize, Serialize};

	#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
	pub struct PerformanceInstance {
		pub name: String,
		pub term: Term,
		pub when: chrono::DateTime<chrono::Utc>,
	}
}

mod attendance {
	use super::Term;
	use serde::{Deserialize, Serialize};

	#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
	pub struct AttendanceInstance {
		pub name: String,
		pub term: Term,
		pub when: chrono::DateTime<chrono::Utc>,
	}
}

mod overrides {
	use super::{AreaDescriptor, AttendanceInstance, CourseInstance, PerformanceInstance};
	use serde::{Deserialize, Serialize};

	#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
	pub struct Override {
		pub path: Vec<PathSegment>,
		pub value: Value,
		pub mode: Mode,
	}

	#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
	pub enum Mode {
		SetResult,
		AllowValue,
	}

	#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
	pub enum Value {
		Course(CourseInstance),
		Area(AreaDescriptor),
		Performance(PerformanceInstance),
		Attendance(AttendanceInstance),
	}

	#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
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
