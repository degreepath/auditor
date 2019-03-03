use crate::area_of_study::AreaType;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AreaDescriptor {
	name: String,
	#[serde(flatten)]
	area_type: AreaType,
	catalog: String,
}
