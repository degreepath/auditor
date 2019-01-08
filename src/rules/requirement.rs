use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct RequirementRule {
    pub requirement: String,
    #[serde(default = "util::serde_false")]
    pub optional: bool,
}
