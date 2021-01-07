use serde::{Deserialize, Serialize};
use std::fmt::Display;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Path(pub Vec<String>);

impl Display for Path {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self.0)
    }
}

impl PartialEq<&[&str]> for Path {
    fn eq(&self, other: &&[&str]) -> bool {
        self.0.as_slice() == *other
    }
}
