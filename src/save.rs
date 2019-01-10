use crate::rules::given::{action, filter, limit, Given, What};

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct SaveBlock {
    pub name: String,
    pub label: String,
    #[serde(flatten)]
    pub given: Given,
    #[serde(default)]
    pub limit: Vec<limit::Limiter>,
    #[serde(rename = "where", default)]
    pub filter: filter::Clause,
    pub what: What,
    #[serde(rename = "do", default, deserialize_with = "action::option_action")]
    pub action: Option<action::Action>,
}

#[cfg(test)]
mod tests {}
