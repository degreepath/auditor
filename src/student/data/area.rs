use crate::area_of_study::AreaType;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AreaDescriptor {
	pub name: String,
	#[serde(flatten)]
	pub area_type: AreaType,
	pub catalog: String,
}
