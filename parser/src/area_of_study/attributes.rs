use std::collections::BTreeMap;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Attributes {
	#[serde(default)]
	pub defaults: Defaults,
	#[serde(default)]
	pub definitions: BTreeMap<String, Definition>,
	#[serde(default)]
	pub courses: BTreeMap<String, Application>,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone, Default)]
pub struct Defaults {
	#[serde(rename="may count for multiple requirements",)]
	may_count_for_multiple_requirements: BoolOrPath,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
enum BoolOrPath {
	Bool(bool),
	Path(Vec<Vec<String>>),
}

impl Default for BoolOrPath {
	fn default() -> Self {
		BoolOrPath::Bool(false)
	}
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Definition {
	#[serde(flatten)]
	pub kind: Mode,
}

pub type Application = BTreeMap<String, Value>;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum Mode {
	Array {
		#[serde(rename = "multiple values can be used")]
		multiple_values_can_be_used: bool,
	},
	// TODO: remove the area_of_study::attributes::Mode::Set variant?
	Set {
		#[serde(rename = "multiple values can be used")]
		multiple_values_can_be_used: bool,
	},
	String,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum Value {
	Vec(Vec<String>),
	Path(Vec<Vec<String>>),
	String(String),
}
