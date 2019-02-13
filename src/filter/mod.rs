use crate::value::WrappedValue;
// use indexmap::IndexMap;
use std::collections::BTreeMap;

mod constant;
mod deserialize;
mod print;
#[cfg(test)]
mod tests;

pub(crate) use deserialize::{deserialize_with, deserialize_with_no_option};

pub type Clause = BTreeMap<String, WrappedValue>;
