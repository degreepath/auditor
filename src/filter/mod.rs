use crate::value::WrappedValue;
use indexmap::IndexMap;

mod constant;
mod deserialize;
mod print;
#[cfg(test)]
mod tests;

pub(crate) use deserialize::{deserialize_with, deserialize_with_no_option};

pub type Clause = IndexMap<String, WrappedValue>;
