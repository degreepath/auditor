use crate::rules::given::action;
use crate::util;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    #[serde(rename = "do", deserialize_with = "util::string_or_struct_parseerror")]
    pub action: action::Action,
}
