#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub struct Clause {
    pub key: String,
    pub value: String,
    pub operation: Op,
}

#[derive(Debug, PartialEq, Serialize, Deserialize, Clone)]
pub enum Op {
    Eq,
    NotEq,
}
