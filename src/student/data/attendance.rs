use super::Term;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AttendanceInstance {
	name: String,
	term: Term,
	when: DateTime<Utc>,
}
