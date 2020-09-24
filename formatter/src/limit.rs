use crate::student::Student;
use crate::to_prose::{ProseOptions, ToProse};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Limit {
    at_most: String,
}

impl ToProse for Limit {
    fn to_prose(
        &self,
        f: &mut std::fmt::Formatter<'_>,
        _student: &Student,
        _options: &ProseOptions,
        _indent: usize,
    ) -> std::fmt::Result {
        write!(f, "at most {}", self.at_most)
    }
}
