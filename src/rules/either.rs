use crate::rules::Rule;

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct EitherRule {
    pub either: (Box<Rule>, Box<Rule>),
}
