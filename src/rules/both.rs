use crate::rules::Rule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct BothRule {
    pub both: (Box<Rule>, Box<Rule>),
}
