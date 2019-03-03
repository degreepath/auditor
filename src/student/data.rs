use serde::{Deserialize, Serialize};

mod area;
mod attendance;
mod course;
mod organization;
mod performance;

pub use area::AreaDescriptor;
pub use attendance::AttendanceInstance;
pub use course::{CourseInstance, CourseType, GradeOption};
pub use organization::OrganizationDescriptor;
pub use performance::PerformanceInstance;

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
			"1" => Ok(Semester::Fall),
			"Interim" => Ok(Semester::Interim),
			"2" => Ok(Semester::Interim),
			"Spring" => Ok(Semester::Spring),
			"3" => Ok(Semester::Spring),
			"Summer Session 1" => Ok(Semester::Summer1),
			"4" => Ok(Semester::Summer1),
			"Summer Session 2" => Ok(Semester::Summer2),
			"5" => Ok(Semester::Summer2),
			"Non-St. Olaf" => Ok(Semester::NonStOlaf),
			"9" => Ok(Semester::NonStOlaf),
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

impl crate::traits::print::Print for Semester {
	fn print(&self) -> crate::traits::print::Result {
		Ok(format!("{}", self))
	}
}
