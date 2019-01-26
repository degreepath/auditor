use indexmap::IndexMap;

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Attributes {
	#[serde(default)]
	pub multicountable: Vec<Vec<Matchable>>,
	#[serde(default)]
	pub courses: IndexMap<CourseReference, Vec<String>>,
}

type CourseReference = String;

#[derive(Debug, PartialEq, Eq, Hash, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Matchable {
	CourseId {course: String},
	Attribute {attribute: String},
	GeReq {gereq: String},
}
