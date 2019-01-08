use crate::rules::Rule;
use crate::save::SaveBlock;
use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Requirement {
    pub name: String,
    pub message: Option<String>,
    #[serde(default = "util::serde_false")]
    pub department_audited: bool,
    pub result: Rule,
    #[serde(default = "util::serde_false")]
    pub contract: bool,
    pub save: Vec<SaveBlock>,
    #[serde(default)]
    pub requirements: Vec<Requirement>,
}
