use super::Term;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct OrganizationDescriptor {
	name: String,
	#[serde(deserialize_with = "crate::util::string_or_struct_parseerror")]
	term: Term,
	role: String,
}
