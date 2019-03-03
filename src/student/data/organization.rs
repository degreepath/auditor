use super::Term;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct OrganizationDescriptor {
	name: String,
	term: Term,
	role: String,
}
