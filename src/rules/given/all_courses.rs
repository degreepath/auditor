use super::{block, common};

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    pub given: String,
    pub what: common::WhatToGive,
    #[serde(default, rename = "where")]
    pub filter: Vec<block::filter::Clause>,
    #[serde(default)]
    pub limit: Vec<block::limit::Limiter>,
    #[serde(rename = "do")]
    pub action: block::action::Action,
}
