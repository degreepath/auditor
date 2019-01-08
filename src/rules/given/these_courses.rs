use super::{block, common};
use crate::rules::course;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Rule {
    pub given: String,
    pub courses: Vec<course::CourseRule>,
    #[serde(rename = "where")]
    pub filter: Vec<block::filter::Clause>,
    pub limit: Vec<block::limit::Limiter>,
    pub what: common::WhatToGive,
    #[serde(rename = "do")]
    pub action: block::action::Action,
}
