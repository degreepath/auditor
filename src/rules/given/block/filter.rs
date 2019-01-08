#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Clause {
    pub key: String,
    pub value: String,
    pub operation: Operator,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Operator {
    EqualTo,
    NotEqualTo,
}
