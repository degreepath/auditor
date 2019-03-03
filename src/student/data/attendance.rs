use super::Term;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AttendanceInstance {
	name: String,
	#[serde(deserialize_with = "crate::util::string_or_struct_parseerror")]
	term: Term,
	when: DateTime<Utc>,
}
