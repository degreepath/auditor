use super::*;
use serde::ser::{SerializeStruct, Serializer};
use serde::Serialize;

impl Serialize for Rule {
	fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
	where
		S: Serializer,
	{
		match &self {
			Rule {
				term: None,
				section: None,
				year: None,
				semester: None,
				lab: None,
				can_match_used: None,
				course,
			} => {
				let mut state = serializer.serialize_struct("Rule", 1)?;
				state.serialize_field("course", course)?;
				state.end()
			}
			_ => {
				let mut state = serializer.serialize_struct("Rule", 7)?;
				state.serialize_field("course", &self.course)?;
				state.serialize_field("term", &self.term)?;
				state.serialize_field("section", &self.section)?;
				state.serialize_field("year", &self.year)?;
				state.serialize_field("semester", &self.semester)?;
				state.serialize_field("lab", &self.lab)?;
				state.serialize_field("can_match_used", &self.can_match_used)?;
				state.end()
			}
		}
	}
}
