use indexmap::IndexMap;

mod deserialize;
mod print;
#[cfg(test)]
mod tests;
mod value;

pub(crate) use deserialize::{deserialize_with, deserialize_with_no_option};

pub use value::{Constant, TaggedValue, Value, WrappedValue};

pub type Clause = IndexMap<String, WrappedValue>;
